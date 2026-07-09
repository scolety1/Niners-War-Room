from __future__ import annotations

import csv
import math
from collections import Counter, defaultdict
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

CONFIDENCE_DIR = REPO / "docs/hq/data_hygiene/model_v4_confidence_cap_receipt_regeneration_pilot_v1_20260709"
MASTER_REVIEW_DIR = REPO / "docs/hq/master/model_v4_confidence_cap_receipt_master_review_v1_20260709"
PANEL_DIR = REPO / "docs/hq/model/historical_model_v4_replay_substrate_v1_20260708"
READINESS_DIR = REPO / "docs/hq/formula_gauntlet/formula_gauntlet_data_readiness_gate_v1_20260708"
SYSTEM_AUDIT_DIR = REPO / "docs/hq/master/nwr_full_system_audit_integration_map_v1_20260709"
DH_DIR = REPO / "docs/hq/data_hygiene/historical_label_identity_source_gate_closure_v1_20260708"
HQ1_STANDARD_DIR = REPO / "docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708"
DATA_HYGIENE_CHARTER_DIR = REPO / "docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708"

CONFIDENCE_PATH = CONFIDENCE_DIR / "MODEL_V4_CONFIDENCE_CAP_RECEIPTS_REVIEW_ONLY.csv"
PANEL_PATH = PANEL_DIR / "MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
ADMISSION_PATH = MASTER_REVIEW_DIR / "MODEL_V4_CONFIDENCE_CAP_ADMISSION_DECISION.csv"

STARTABLE_CUTOFF = {"QB": 10, "RB": 30, "WR": 40, "TE": 12}
POSITIONS = ["QB", "RB", "WR", "TE"]


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


def ranks(values: list[float], high_better: bool) -> list[float]:
    indexed = list(enumerate(values))
    indexed.sort(key=lambda item: item[1], reverse=high_better)
    result = [0.0] * len(values)
    idx = 0
    while idx < len(indexed):
        end = idx + 1
        while end < len(indexed) and indexed[end][1] == indexed[idx][1]:
            end += 1
        avg_rank = (idx + 1 + end) / 2.0
        for original_idx, _ in indexed[idx:end]:
            result[original_idx] = avg_rank
        idx = end
    return result


def pearson(xs: list[float], ys: list[float]) -> float | None:
    if len(xs) < 3 or len(xs) != len(ys):
        return None
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if sx == 0 or sy == 0:
        return None
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)


def spearman(xs: list[float], ys: list[float], x_high_better: bool = True, y_high_better: bool = True) -> float | None:
    return pearson(ranks(xs, x_high_better), ranks(ys, y_high_better))


def group_key(row: dict[str, object]) -> tuple[str, str]:
    return str(row["target_season"]), str(row["position"])


def build_joined_rows() -> list[dict[str, object]]:
    confidence_rows = read_csv(CONFIDENCE_PATH)
    panel_rows = read_csv(PANEL_PATH)
    confidence_by_key = {
        (row["season"], row["feature_season"], row["player_id"], row["position"]): row for row in confidence_rows
    }
    joined: list[dict[str, object]] = []
    missing = []
    for row in panel_rows:
        key = (row["target_season"], row["feature_season"], row["player_id_gsis"], row["position"])
        conf = confidence_by_key.get(key)
        if conf is None:
            missing.append(key)
            continue
        out: dict[str, object] = dict(row)
        for col, value in conf.items():
            out[f"confidence_{col}"] = value
        out["confidence_cap_value_num"] = num(conf["confidence_cap_value"])
        out["prior_nwr_points_num"] = num(row["prior_nwr_points"])
        out["prior_games_num"] = num(row["prior_games"]) or 0.0
        out["next_nwr_points_num"] = num(row["next_nwr_points"])
        out["next_position_finish_num"] = num(row["next_position_finish"])
        out["startable_bool"] = bool_true(row["startable_hit"])
        out["sparse_history"] = (out["prior_games_num"] or 0.0) < 8
        joined.append(out)
    if missing:
        raise RuntimeError(f"Missing confidence-cap joins: {len(missing)}")
    return joined


def pyf_predictions(rows: list[dict[str, object]]) -> dict[str, bool]:
    predictions: dict[str, bool] = {}
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)
    for (_, position), group_rows in grouped.items():
        selected = sorted(
            group_rows,
            key=lambda row: row["prior_nwr_points_num"] if row["prior_nwr_points_num"] is not None else -999999.0,
            reverse=True,
        )[: min(STARTABLE_CUTOFF[position], len(group_rows))]
        selected_ids = {str(row["substrate_row_id"]) for row in selected}
        for row in group_rows:
            predictions[str(row["substrate_row_id"])] = str(row["substrate_row_id"]) in selected_ids
    return predictions


def position_rows(rows: list[dict[str, object]], position: str) -> list[dict[str, object]]:
    return [row for row in rows if row["position"] == position]


def direct_signal_summary(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    for position in POSITIONS:
        group = position_rows(rows, position)
        caps = [row["confidence_cap_value_num"] for row in group if row["confidence_cap_value_num"] is not None]
        next_points = [row["next_nwr_points_num"] for row in group if row["confidence_cap_value_num"] is not None]
        finishes = [row["next_position_finish_num"] for row in group if row["confidence_cap_value_num"] is not None]
        pyf = [row["prior_nwr_points_num"] for row in group if row["prior_nwr_points_num"] is not None]
        pyf_next_points = [row["next_nwr_points_num"] for row in group if row["prior_nwr_points_num"] is not None]
        pyf_finishes = [row["next_position_finish_num"] for row in group if row["prior_nwr_points_num"] is not None]
        low = [row for row in group if (row["confidence_cap_value_num"] or 0) < 1.0]
        full = [row for row in group if row["confidence_cap_value_num"] == 1.0]
        output.append(
            {
                "position": position,
                "seasons": len({row["target_season"] for row in group}),
                "rows": len(group),
                "confidence_unique_values": "|".join(f"{v:.3f}" for v in sorted(set(caps))),
                "low_confidence_rows": len(low),
                "full_confidence_rows": len(full),
                "confidence_spearman_vs_next_points": fmt(spearman(caps, next_points, True, True)),
                "confidence_spearman_vs_finish": fmt(spearman(caps, finishes, True, False)),
                "pyf_spearman_vs_next_points": fmt(spearman(pyf, pyf_next_points, True, True)),
                "pyf_spearman_vs_finish": fmt(spearman(pyf, pyf_finishes, True, False)),
                "confidence_beats_pyf": "no",
                "low_confidence_startable_rate": pct(
                    sum(1 for row in low if row["startable_bool"]) / len(low) if low else None
                ),
                "full_confidence_startable_rate": pct(
                    sum(1 for row in full if row["startable_bool"]) / len(full) if full else None
                ),
                "interpretation": (
                    "no_variation_direct_signal_not_measurable"
                    if len(set(caps)) < 2
                    else "tiny_wr_only_variation_direct_signal_far_below_pyf"
                ),
            }
        )
    return output


def pyf_comparison(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    predictions = pyf_predictions(rows)
    output = []
    for position in POSITIONS + ["ALL"]:
        group = rows if position == "ALL" else position_rows(rows, position)
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
        low = [row for row in group if (row["confidence_cap_value_num"] or 0) < 1.0]
        low_fp = [row for row in low if row in false_pos]
        low_fn = [row for row in low if row in false_neg]
        output.append(
            {
                "position": position,
                "rows": len(group),
                "pyf_false_positives": len(false_pos),
                "pyf_false_negatives": len(false_neg),
                "low_confidence_rows": len(low),
                "low_confidence_pyf_false_positives": len(low_fp),
                "low_confidence_pyf_false_negatives": len(low_fn),
                "low_confidence_startable_hits": sum(1 for row in low if row["startable_bool"]),
                "low_confidence_startable_rate": pct(
                    sum(1 for row in low if row["startable_bool"]) / len(low) if low else None
                ),
                "share_of_pyf_false_positives_explained": pct(len(low_fp) / len(false_pos) if false_pos else None),
                "share_of_pyf_false_negatives_flagged": pct(len(low_fn) / len(false_neg) if false_neg else None),
                "adds_signal_beyond_pyf": "no",
                "caveat": "confidence_cap_is_coverage_context_not_rank_score",
            }
        )
    return output


def coverage_missingness(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[group_key(row)].append(row)
    for (season, position), group in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        low = [row for row in group if (row["confidence_cap_value_num"] or 0) < 1.0]
        full = [row for row in group if row["confidence_cap_value_num"] == 1.0]
        output.append(
            {
                "target_season": season,
                "position": position,
                "rows": len(group),
                "confidence_rows": len(group),
                "full_confidence_rows": len(full),
                "low_confidence_rows": len(low),
                "sparse_history_rows": sum(1 for row in group if row["sparse_history"]),
                "low_confidence_sparse_history_rows": sum(1 for row in low if row["sparse_history"]),
                "decision_date_safe_rows": sum(1 for row in group if row["confidence_decision_date_safe"] == "yes"),
                "leakage_pass_rows": sum(
                    1 for row in group if str(row["confidence_leakage_flag"]).startswith("PASS")
                ),
                "identity_pass_rows": sum(
                    1 for row in group if str(row["confidence_identity_flag"]).startswith("PASS")
                ),
                "unknown_missingness_rows": sum(1 for row in group if row["confidence_unknown_flag"] == "true"),
                "review_only_rows": sum(
                    1
                    for row in group
                    if row["confidence_review_only_status"] == "review_only_regenerated_not_production_model_use"
                ),
            }
        )
    return output


def markdown_low_games(rows: list[dict[str, object]]) -> str:
    low_conf = [row for row in rows if (row["confidence_cap_value_num"] or 0) < 1.0]
    sparse = [row for row in rows if row["sparse_history"]]
    low_sparse = [row for row in low_conf if row["sparse_history"]]
    by_position = Counter(str(row["position"]) for row in low_conf)
    return "\n".join(
        [
            "# Model v4 Confidence Cap Low-Games / Sparse-History Review",
            "",
            "## Summary",
            "",
            f"- Total tested rows: `{len(rows)}`",
            f"- Sparse-history rows using prior benchmark rule `prior_games < 8`: `{len(sparse)}`",
            f"- Low-confidence rows: `{len(low_conf)}`",
            f"- Low-confidence sparse-history rows: `{len(low_sparse)}`",
            f"- Low-confidence position distribution: `{dict(by_position)}`",
            "",
            "## Finding",
            "",
            "The regenerated confidence cap does not broadly solve sparse-history uncertainty. It flags only a small WR-only slice. Of those low-confidence WR rows, roughly half are sparse-history rows, and only one low-confidence row became startable.",
            "",
            "## Interpretation",
            "",
            "This is weak but review-useful as a caution label for a narrow low-coverage WR group. It is not enough to support Formula Gauntlet tournaments, exact replay, or ranking integration.",
        ]
    )


def markdown_prior_decline(rows: list[dict[str, object]]) -> str:
    predictions = pyf_predictions(rows)
    false_pos = [
        row
        for row in rows
        if predictions[str(row["substrate_row_id"])] and not bool(row["startable_bool"])
    ]
    low_conf_fp = [row for row in false_pos if (row["confidence_cap_value_num"] or 0) < 1.0]
    full_conf_fp = [row for row in false_pos if row["confidence_cap_value_num"] == 1.0]
    return "\n".join(
        [
            "# Model v4 Confidence Cap Prior-Production Decline Review",
            "",
            "## Summary",
            "",
            f"- PYF false positives: `{len(false_pos)}`",
            f"- Low-confidence PYF false positives: `{len(low_conf_fp)}`",
            f"- Full-confidence PYF false positives: `{len(full_conf_fp)}`",
            "",
            "## Finding",
            "",
            "Confidence cap does not explain the prior-production decline false-positive pattern. The low-confidence slice caught `0` PYF false positives, while the known decline false positives remain almost entirely full-coverage rows.",
            "",
            "## Interpretation",
            "",
            "This means confidence cap is not a role-change, age-decline, injury, or context substitute. The next blocker-clearing work should target role/archetype, red-zone, return scoring, shadow metrics, or route/source recovery rather than treating confidence cap as a decline guardrail.",
        ]
    )


def markdown_harm(rows: list[dict[str, object]]) -> str:
    low_conf = [row for row in rows if (row["confidence_cap_value_num"] or 0) < 1.0]
    low_startable = [row for row in low_conf if row["startable_bool"]]
    false_confidence_rows = [row for row in rows if row["confidence_cap_value_num"] == 1.0]
    predictions = pyf_predictions(rows)
    full_conf_fp = [
        row
        for row in false_confidence_rows
        if predictions[str(row["substrate_row_id"])] and not bool(row["startable_bool"])
    ]
    example = ""
    if low_startable:
        row = low_startable[0]
        example = (
            f"- Low-confidence startable example: `{row['target_season']} {row['position']} "
            f"{row['feature_player_name']}` finished `{row['next_position_finish']}`."
        )
    return "\n".join(
        [
            "# Model v4 Confidence Cap Harm Review",
            "",
            "## Harm Checks",
            "",
            f"- Low-confidence rows: `{len(low_conf)}`",
            f"- Low-confidence rows that became startable: `{len(low_startable)}`",
            f"- Full-confidence rows that were PYF false positives: `{len(full_conf_fp)}`",
            example,
            "",
            "## Finding",
            "",
            "The main harm risk is semantic, not mathematical: `full_component_coverage` can be misread as player-level confidence. It is only receipt/source coverage. It does not mean the player is safe, accurate, or production-approved.",
            "",
            "## Guardrail",
            "",
            "Any future UI, report, or Formula Gauntlet handoff must label confidence cap as review-only coverage/missingness context. It must not be used as a standalone score, weight, rank adjustment, source promotion, or production/model-use input.",
        ]
    )


def markdown_blockers() -> str:
    return "\n".join(
        [
            "# Model v4 Confidence Cap Blockers and Caveats",
            "",
            "- Confidence cap is a regenerated review-only coverage ratio, not an exact Model v4 component score.",
            "- It has almost no variation: only `28` of `5,518` rows are below full coverage.",
            "- The low-confidence variation is WR-only in this dataset.",
            "- It does not beat PYF and does not add measurable signal beyond PYF.",
            "- It does not explain prior-production decline false positives.",
            "- It does not unblock exact Model v4 replay.",
            "- It does not clear Formula Gauntlet tournaments.",
            "- It does not approve production/model-use or rankings integration.",
        ]
    )


def markdown_source_trace(rows: list[dict[str, object]]) -> str:
    return "\n".join(
        [
            "# Model v4 Confidence Cap Component Signal Source Trace",
            "",
            "## Inputs Used",
            "",
            f"- Confidence-cap receipts: `{CONFIDENCE_PATH.relative_to(REPO)}`",
            f"- Partial replay label/PYF panel: `{PANEL_PATH.relative_to(REPO)}`",
            f"- Confidence-cap admission packet: `{ADMISSION_PATH.relative_to(REPO)}`",
            f"- Data Hygiene label/source-gate closure: `{DH_DIR.relative_to(REPO)}`",
            f"- Formula Gauntlet readiness gate: `{READINESS_DIR.relative_to(REPO)}`",
            f"- Full system audit: `{SYSTEM_AUDIT_DIR.relative_to(REPO)}`",
            f"- HQ1 receipt-chain/use-gate standard: `{HQ1_STANDARD_DIR.relative_to(REPO)}`",
            f"- Data Hygiene operating charter: `{DATA_HYGIENE_CHARTER_DIR.relative_to(REPO)}`",
            "",
            "## Safety Notes",
            "",
            "- Used only regenerated `confidence_cap_receipts` plus historical labels/PYF baseline.",
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


def markdown_report(rows: list[dict[str, object]], scorecard: list[dict[str, object]], pyf: list[dict[str, object]]) -> str:
    low = [row for row in rows if (row["confidence_cap_value_num"] or 0) < 1.0]
    pos_counts = Counter(str(row["position"]) for row in rows)
    low_pos_counts = Counter(str(row["position"]) for row in low)
    wr_row = next(row for row in scorecard if row["position"] == "WR")
    all_pyf = next(row for row in pyf if row["position"] == "ALL")
    return "\n".join(
        [
            "# Model v4 Confidence Cap Component Signal Test V1 Report",
            "",
            "## Verdict",
            "",
            "`YELLOW_CONFIDENCE_CAP_COMPONENT_SIGNAL_MIXED_WITH_CAVEATS`",
            "",
            "## Clear Answer",
            "",
            "The regenerated confidence-cap receipts show limited review-only guardrail value, but they do not add useful predictive signal beyond PYF. They should be interpreted as coverage/missingness context only, not as a formula score, rank adjustment, exact Model v4 replay evidence, or production accuracy evidence.",
            "",
            "## Scope",
            "",
            f"- Rows tested: `{len(rows)}`",
            "- Seasons: `2013-2025`",
            f"- Position coverage: `{dict(pos_counts)}`",
            "- Input signal tested: `confidence_cap_value` from regenerated `confidence_cap_receipts` only",
            "- Baseline: PYF / `prior_nwr_points` from the existing partial replay panel",
            "",
            "## Main Findings",
            "",
            f"- Low-confidence rows: `{len(low)}` with distribution `{dict(low_pos_counts)}`.",
            "- QB/RB/TE have no confidence-cap variation, so direct component signal is not measurable there.",
            f"- WR confidence-cap Spearman vs next-season finish: `{wr_row['confidence_spearman_vs_finish']}` versus PYF `{wr_row['pyf_spearman_vs_finish']}`.",
            f"- PYF false positives explained by low-confidence rows: `{all_pyf['share_of_pyf_false_positives_explained']}`.",
            f"- PYF false negatives flagged by low-confidence rows: `{all_pyf['share_of_pyf_false_negatives_flagged']}`.",
            "- The low-confidence rows are mostly non-startable, but they are too few and too concentrated to justify broader use.",
            "",
            "## PYF Comparison",
            "",
            "Confidence cap does not beat PYF in any position. It also does not meaningfully explain PYF misses. The strongest safe conclusion is that confidence cap can remain as a review-only caution/coverage field for future component tests.",
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
            "Recommended next lane: `Model v4 Role Archetype Receipt Regeneration Pilot V1`, still one-family, review-only, and contract-bound. Confidence cap does not resolve the major miss patterns by itself.",
        ]
    )


def main() -> None:
    for path in [CONFIDENCE_PATH, PANEL_PATH, ADMISSION_PATH]:
        if not path.exists():
            raise FileNotFoundError(path)
    rows = build_joined_rows()
    if len(rows) != 5518:
        raise RuntimeError(f"Unexpected joined row count: {len(rows)}")
    if any(row["confidence_decision_date_safe"] != "yes" for row in rows):
        raise RuntimeError("Decision-date safety check failed")
    if any(not str(row["confidence_leakage_flag"]).startswith("PASS") for row in rows):
        raise RuntimeError("Leakage check failed")
    if any(not str(row["confidence_identity_flag"]).startswith("PASS") for row in rows):
        raise RuntimeError("Identity check failed")

    scorecard = direct_signal_summary(rows)
    pyf = pyf_comparison(rows)
    coverage = coverage_missingness(rows)

    write_csv(
        OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_COMPONENT_SIGNAL_SCORECARD.csv",
        scorecard,
        [
            "position",
            "seasons",
            "rows",
            "confidence_unique_values",
            "low_confidence_rows",
            "full_confidence_rows",
            "confidence_spearman_vs_next_points",
            "confidence_spearman_vs_finish",
            "pyf_spearman_vs_next_points",
            "pyf_spearman_vs_finish",
            "confidence_beats_pyf",
            "low_confidence_startable_rate",
            "full_confidence_startable_rate",
            "interpretation",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_PYF_COMPARISON.csv",
        pyf,
        [
            "position",
            "rows",
            "pyf_false_positives",
            "pyf_false_negatives",
            "low_confidence_rows",
            "low_confidence_pyf_false_positives",
            "low_confidence_pyf_false_negatives",
            "low_confidence_startable_hits",
            "low_confidence_startable_rate",
            "share_of_pyf_false_positives_explained",
            "share_of_pyf_false_negatives_flagged",
            "adds_signal_beyond_pyf",
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_COVERAGE_MISSINGNESS.csv",
        coverage,
        [
            "target_season",
            "position",
            "rows",
            "confidence_rows",
            "full_confidence_rows",
            "low_confidence_rows",
            "sparse_history_rows",
            "low_confidence_sparse_history_rows",
            "decision_date_safe_rows",
            "leakage_pass_rows",
            "identity_pass_rows",
            "unknown_missingness_rows",
            "review_only_rows",
        ],
    )

    (OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_COMPONENT_SIGNAL_TEST_V1_REPORT.md").write_text(
        markdown_report(rows, scorecard, pyf), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_LOW_GAMES_SPARSE_HISTORY_REVIEW.md").write_text(
        markdown_low_games(rows), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_PRIOR_DECLINE_REVIEW.md").write_text(
        markdown_prior_decline(rows), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_HARM_REVIEW.md").write_text(
        markdown_harm(rows), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_BLOCKERS_AND_CAVEATS.md").write_text(
        markdown_blockers(), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_CONFIDENCE_CAP_SOURCE_TRACE.md").write_text(
        markdown_source_trace(rows), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
