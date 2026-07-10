from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO = OUT_DIR.parents[3]
HANDOFF_DIR = Path(r"C:\NWR_REVIEW\nwr_post_injury_scoreboard_handoff_v2_20260709\nwr_post_injury_scoreboard_handoff_v2_20260709")
REMOTE_HEAD = "b125be9ee73f1adc3487c1fa69ae954e8e49790f"
INJURY_COMMIT = "168969cffe7a2cc6fe237231cfdc931fc6805e7f"
SNAP_DEPTH_REFERENCE = 0.763
FULL_HISTORY_REFERENCE = 0.755

SCOREBOARD_FIELDS = [
    "scoreboard_type",
    "lane",
    "candidate_id",
    "base_formula",
    "ingredient_set",
    "row_count",
    "seasons",
    "spearman",
    "pyf_same_row",
    "formula_alone_same_row",
    "delta_vs_pyf",
    "delta_vs_0755",
    "delta_vs_snap_depth_0763",
    "full_history_comparable",
    "broad_window_comparable",
    "partial_window_only",
    "use_decision",
    "caveats",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for row in rows:
            for key in row:
                if key not in fields:
                    fields.append(key)
    with open(fs_path(path), "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(fs_path(path), "w", encoding="utf-8", newline="\n") as f:
        f.write(text.strip() + "\n")


def fs_path(path: Path) -> str:
    text = str(path)
    if len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.3f}"


def as_int(value: Any) -> int:
    val = as_float(value)
    return int(val) if val is not None else 0


def parse_seasons(text: str) -> set[int]:
    out = set()
    for part in str(text or "").split("|"):
        if part.strip().isdigit():
            out.add(int(part))
    return out


def board_type(lane: str, row: dict[str, str], registry_row: dict[str, str] | None) -> str:
    seasons = parse_seasons(row.get("seasons", ""))
    row_count = as_int(row.get("row_count"))
    ingredient_blob = " ".join([
        row.get("ingredient_set", ""),
        row.get("ingredient_fields", ""),
        row.get("run_id", ""),
        (registry_row or {}).get("comparability_flag", ""),
        (registry_row or {}).get("full_history_comparable_flag", ""),
    ]).lower()
    if "partial_window" in ingredient_blob or "ffop" in ingredient_blob or "ngs" in ingredient_blob:
        return "partial_window"
    if lane == "PFR RB broken tackle":
        return "partial_window"
    if lane == "nflverse snap/depth role" and row_count >= 5000 and 2014 in seasons and 2013 not in seasons:
        return "broad_window"
    if "broad_window" in ingredient_blob:
        return "broad_window"
    if row_count >= 5000 and 2013 in seasons and 2025 in seasons:
        return "full_history"
    return "partial_window"


def normalize_row(lane: str, row: dict[str, str], registry_row: dict[str, str] | None = None) -> dict[str, str]:
    spearman = as_float(row.get("overall_spearman"))
    pyf_delta = as_float(row.get("pyf_delta"))
    seed_delta = as_float(row.get("cluster_seed_delta"))
    board = board_type(lane, row, registry_row)
    pyf_same = spearman - pyf_delta if spearman is not None and pyf_delta is not None else None
    formula_same = spearman - seed_delta if spearman is not None and seed_delta is not None else None
    full = board == "full_history"
    broad = board == "broad_window"
    partial = board == "partial_window"
    if broad:
        snap_delta = spearman - SNAP_DEPTH_REFERENCE if spearman is not None else None
    elif lane == "point-in-time injury availability" and spearman is not None and as_int(row.get("row_count")) >= 5000:
        snap_delta = spearman - SNAP_DEPTH_REFERENCE
    else:
        snap_delta = None
    caveats = []
    if partial:
        caveats.append("partial-window; do not compare directly to full-history plateau")
    if broad:
        caveats.append("broad-window comparable; missing earliest full-history coverage")
    if lane == "point-in-time injury availability":
        caveats.append("availability context only; not injury prediction")
    if lane == "nflverse EPA/opportunity":
        caveats.append("EPA-only did not beat .755; combos with ffop inherit partial-window caveat")
    if lane == "nflverse receiving opportunity":
        caveats.append("full-history receiving rows tied/trailed .755; ffop combos are partial")
    if lane == "nflverse snap/depth role":
        caveats.append("best lift is broad-window 2014-2025, not full 2013-2025")
    return {
        "scoreboard_type": board,
        "lane": lane,
        "candidate_id": row.get("run_id", ""),
        "base_formula": row.get("base_formula", ""),
        "ingredient_set": row.get("ingredient_set", ""),
        "row_count": row.get("row_count", ""),
        "seasons": row.get("seasons", ""),
        "spearman": fmt(spearman),
        "pyf_same_row": fmt(pyf_same),
        "formula_alone_same_row": fmt(formula_same),
        "delta_vs_pyf": fmt(pyf_delta),
        "delta_vs_0755": fmt(spearman - FULL_HISTORY_REFERENCE if spearman is not None else None),
        "delta_vs_snap_depth_0763": fmt(snap_delta),
        "full_history_comparable": str(full).lower(),
        "broad_window_comparable": str(broad).lower(),
        "partial_window_only": str(partial).lower(),
        "use_decision": row.get("use_decision", ""),
        "caveats": "; ".join(caveats),
    }


def best(rows: list[dict[str, str]]) -> dict[str, str] | None:
    scored = [r for r in rows if as_float(r.get("spearman")) is not None]
    if not scored:
        return None
    return max(scored, key=lambda r: as_float(r["spearman"]) or -1)


def registry(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    return {r["run_id"]: r for r in read_csv(path)}


def load_scored_rows() -> list[dict[str, str]]:
    scored_sources = [
        (
            "ffopportunity / NGS autonomous V2",
            REPO / "docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/AUTONOMOUS_ALL_RESULTS_REQUIRED_SCHEMA.csv",
            REPO / "docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/AUTONOMOUS_PREDECLARED_TEST_REGISTRY.csv",
        ),
        (
            "nflverse EPA/opportunity",
            REPO / "docs/hq/model/nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709/NFLVERSE_EPA_OPPORTUNITY_ALL_RESULTS_REQUIRED_SCHEMA.csv",
            REPO / "docs/hq/model/nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709/NFLVERSE_EPA_OPPORTUNITY_PREDECLARED_TEST_REGISTRY.csv",
        ),
        (
            "nflverse receiving opportunity",
            REPO / "docs/hq/model/nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709/NFLVERSE_RECEIVING_OPPORTUNITY_ALL_RESULTS_REQUIRED_SCHEMA.csv",
            REPO / "docs/hq/model/nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709/NFLVERSE_RECEIVING_OPPORTUNITY_PREDECLARED_TEST_REGISTRY.csv",
        ),
        (
            "nflverse snap/depth role",
            REPO / "docs/hq/model/nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709/NFLVERSE_SNAP_DEPTH_ROLE_ALL_RESULTS_REQUIRED_SCHEMA.csv",
            REPO / "docs/hq/model/nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709/NFLVERSE_SNAP_DEPTH_ROLE_PREDECLARED_TEST_REGISTRY.csv",
        ),
        (
            "point-in-time injury availability",
            REPO / "docs/hq/model/point_in_time_injury_availability_data_mart_gate_v1_20260709/POINT_IN_TIME_INJURY_AVAILABILITY_ALL_RESULTS_REQUIRED_SCHEMA.csv",
            REPO / "docs/hq/model/point_in_time_injury_availability_data_mart_gate_v1_20260709/POINT_IN_TIME_INJURY_AVAILABILITY_PREDECLARED_TEST_REGISTRY.csv",
        ),
    ]
    out: list[dict[str, str]] = []
    for lane, result_path, registry_path in scored_sources:
        reg = registry(registry_path)
        for row in read_csv(result_path):
            if as_float(row.get("overall_spearman")) is None:
                continue
            out.append(normalize_row(lane, row, reg.get(row.get("run_id", ""))))
    out.append(
        {
            "scoreboard_type": "partial_window",
            "lane": "PFR RB broken tackle",
            "candidate_id": "PFR_RB_BROKEN_TACKLE_RAW_COMPONENT",
            "base_formula": "ingredient-only",
            "ingredient_set": "pfr_rb_broken_tackle",
            "row_count": "716",
            "seasons": "2019|2020|2021|2022|2023|2024|2025",
            "spearman": "0.595",
            "pyf_same_row": "0.655",
            "formula_alone_same_row": "",
            "delta_vs_pyf": "-0.060",
            "delta_vs_0755": "-0.160",
            "delta_vs_snap_depth_0763": "",
            "full_history_comparable": "false",
            "broad_window_comparable": "false",
            "partial_window_only": "true",
            "use_decision": "descriptive",
            "caveats": "RB-only 2019-2025 lagged subset; accepted as no incremental formula signal",
        }
    )
    return out


def top_n(rows: list[dict[str, str]], n: int = 25) -> list[dict[str, str]]:
    return sorted(rows, key=lambda r: as_float(r.get("spearman")) or -1, reverse=True)[:n]


def candidate_summary(full: list[dict[str, str]], broad: list[dict[str, str]], partial: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for board, board_rows in [("full_history", full), ("broad_window", broad), ("partial_window", partial)]:
        b = best(board_rows)
        if b:
            rows.append({
                "scoreboard_type": board,
                "best_candidate_id": b["candidate_id"],
                "lane": b["lane"],
                "spearman": b["spearman"],
                "row_count": b["row_count"],
                "seasons": b["seasons"],
                "delta_vs_pyf": b["delta_vs_pyf"],
                "delta_vs_0755": b["delta_vs_0755"],
                "delta_vs_snap_depth_0763": b["delta_vs_snap_depth_0763"],
                "use_decision": b["use_decision"],
                "caveats": b["caveats"],
            })
    return rows


def same_row_baseline_rows(all_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    watch_ids = {
        "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_AVAIL_CAVEAT_INVERSE_PCT100",
        "GAUNTLET_081_DECLINE_SMALL_LATE_GUARD_THREE__PLUS_SNAPDEPTH_SNAP_NOT_LOW_PCT100",
        "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_AVAIL_FFOP_PCT025_025",
        "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_RECOPP_WOPR_EPA_FFOP_PCT025_025_050",
        "GAUNTLET_083_DECLINE_DECLINE_COMBO_GUARD__PLUS_FFOPPORTUNITY_PCT10",
        "PFR_RB_BROKEN_TACKLE_RAW_COMPONENT",
    }
    selected = [r for r in all_rows if r["candidate_id"] in watch_ids]
    for board in ["full_history", "broad_window", "partial_window"]:
        b = best([r for r in all_rows if r["scoreboard_type"] == board])
        if b and b not in selected:
            selected.append(b)
    return [
        {
            "candidate_id": r["candidate_id"],
            "scoreboard_type": r["scoreboard_type"],
            "lane": r["lane"],
            "spearman": r["spearman"],
            "pyf_same_row": r["pyf_same_row"],
            "formula_alone_same_row": r["formula_alone_same_row"],
            "delta_vs_pyf": r["delta_vs_pyf"],
            "delta_vs_0755": r["delta_vs_0755"],
            "delta_vs_snap_depth_0763": r["delta_vs_snap_depth_0763"],
            "row_count": r["row_count"],
            "seasons": r["seasons"],
            "caveats": r["caveats"],
        }
        for r in selected
    ]


def status_rows() -> list[dict[str, str]]:
    return [
        {
            "lane": "PFR RB broken tackle",
            "ingredient": "pfr_rb_broken_tackle",
            "status": "AVAILABLE_REVIEW_ONLY_DESCRIPTIVE_ONLY",
            "best_result": "0.595 vs PYF 0.655 same rows",
            "next_use_decision": "closed as priority formula ingredient; descriptive RB slice only",
        },
        {
            "lane": "nflverse advanced ingredient audit",
            "ingredient": "advanced ingredient inventory",
            "status": "AVAILABLE_REVIEW_ONLY_DESCRIPTIVE_ONLY",
            "best_result": "ffopportunity identified as next executable lane",
            "next_use_decision": "audit complete; use as source trace only",
        },
        {
            "lane": "ffopportunity / NGS autonomous V2",
            "ingredient": "ffopportunity + NGS",
            "status": "AVAILABLE_BUT_PARTIAL_WINDOW_ONLY",
            "best_result": "0.790 partial-window formula x ffopportunity",
            "next_use_decision": "promising interaction context; no full-history claim",
        },
        {
            "lane": "nflverse EPA/opportunity",
            "ingredient": "EPA/opportunity",
            "status": "AVAILABLE_REVIEW_ONLY_INTERACTION_CONTEXT",
            "best_result": "0.747 full-history EPA x formula; 0.789 partial ffop combo",
            "next_use_decision": "do not run EPA-only branch",
        },
        {
            "lane": "nflverse receiving opportunity",
            "ingredient": "receiving opportunity",
            "status": "AVAILABLE_REVIEW_ONLY_INTERACTION_CONTEXT",
            "best_result": "0.755 full-history tie; 0.790 partial combo",
            "next_use_decision": "use as context in bounded combos only",
        },
        {
            "lane": "nflverse snap/depth role",
            "ingredient": "snap/depth role",
            "status": "AVAILABLE_REVIEW_ONLY_ADDITIVE_SIGNAL",
            "best_result": "0.763 broad-window 2014-2025 rows 5122",
            "next_use_decision": "best broad-window non-V2 sidecar; still not production/ranking",
        },
        {
            "lane": "point-in-time injury availability",
            "ingredient": "injury/availability",
            "status": "AVAILABLE_REVIEW_ONLY_GUARDRAIL_CONTEXT",
            "best_result": "0.757 broad/full; 0.789 partial ffop combo",
            "next_use_decision": "guardrail/context only; did not beat snap/depth .763",
        },
        {
            "lane": "Historical Market / ADP",
            "ingredient": "market/adp",
            "status": "PARK_FOR_LATER",
            "best_result": "not yet source/as-of gated",
            "next_use_decision": "recommended next data lane after normalization",
        },
    ]


def make_reports(full: list[dict[str, str]], broad: list[dict[str, str]], partial: list[dict[str, str]], best_rows: list[dict[str, str]]) -> None:
    best_full = best(full)
    best_broad = best(broad)
    best_partial = best(partial)
    material_full = bool(best_full and (as_float(best_full["spearman"]) or 0) >= 0.760)
    beats_snap_comparable = bool(best_broad and (as_float(best_broad["spearman"]) or 0) > SNAP_DEPTH_REFERENCE)
    verdict = "YELLOW_SCOREBOARD_NORMALIZED_RANKING_SIM_NOT_READY"
    if not full or not broad or not partial:
        verdict = "RED_SCOREBOARD_NORMALIZATION_BLOCKED"
    write_md(
        OUT_DIR / "INGREDIENT_SCOREBOARD_NORMALIZATION_BEST_CANDIDATE_CONSOLIDATION_V1_REPORT.md",
        f"""
# Ingredient Scoreboard Normalization / Best Candidate Consolidation V1 Report

## Verdict

`{verdict}`

## Scope

This packet normalizes accepted ingredient results into three separate scoreboards: full-history comparable, broad-window comparable, and partial-window modern. It prevents partial ffopportunity/NGS windows from being compared directly against the full-history `.755` plateau or the snap/depth broad-window `.763` reference.

## Lanes Included

- PFR RB broken tackle
- nflverse advanced ingredient audit
- ffopportunity / NGS autonomous V2
- nflverse EPA/opportunity
- nflverse receiving opportunity
- nflverse snap/depth role
- point-in-time injury availability

## Best By Scoreboard

- Full-history best: `{best_full['candidate_id'] if best_full else ''}` from `{best_full['lane'] if best_full else ''}`, Spearman `{best_full['spearman'] if best_full else ''}`, rows `{best_full['row_count'] if best_full else ''}`.
- Broad-window best: `{best_broad['candidate_id'] if best_broad else ''}` from `{best_broad['lane'] if best_broad else ''}`, Spearman `{best_broad['spearman'] if best_broad else ''}`, rows `{best_broad['row_count'] if best_broad else ''}`.
- Partial-window best: `{best_partial['candidate_id'] if best_partial else ''}` from `{best_partial['lane'] if best_partial else ''}`, Spearman `{best_partial['spearman'] if best_partial else ''}`, rows `{best_partial['row_count'] if best_partial else ''}`.

## Interpretation

- No result materially beats the full-history `.755` plateau. Injury/availability reaches `.757`, but the lift is only about `.002` and does not beat the stronger snap/depth broad-window reference.
- Snap/depth remains the best broad-window additive result at `.763` on `2014-2025`, `5,122` rows.
- Partial-window modern combinations remain promising around `.789-.790`, but they depend on ffopportunity/NGS-era windows and are not full-history-comparable.
- No comparable row set materially beats snap/depth `.763`.
- Review-only ranking simulation is not justified.

## Next Lane

Recommended next single lane: `Historical Market / ADP Source Gate and Data Mart Join V1`.

This should be a source/as-of gate and sidecar join lane, not a ranking simulation and not production model-use.

## Gates Preserved

- Production/model-use remains blocked.
- Rankings integration remains blocked.
- App/runtime behavior changed: no.
- Push/merge performed: no.
- Source promotion: no.
- Canonical `local_exports` mutation: no.
""",
    )
    write_md(
        OUT_DIR / "INGREDIENT_COMBINATION_PROMISING_BUT_PARTIAL.md",
        f"""
# Ingredient Combination Promising But Partial

The best partial-window results remain clustered around ffopportunity-era combinations:

- `{best_partial['candidate_id'] if best_partial else ''}` Spearman `{best_partial['spearman'] if best_partial else ''}`, rows `{best_partial['row_count'] if best_partial else ''}`, seasons `{best_partial['seasons'] if best_partial else ''}`.

These results are promising for future modern-window review, but they are not full-history-comparable and cannot justify ranking simulation, production/model-use, or a claim that the full `.755` plateau has been broken.
""",
    )
    write_md(
        OUT_DIR / "RANKING_SIMULATION_READINESS_DECISION.md",
        f"""
# Ranking Simulation Readiness Decision

Decision: `NOT_READY`.

Reason:

- Full-history normalized results do not materially beat `.755`.
- Broad-window snap/depth is useful at `.763`, but it is not complete `2013-2025` and no comparable row set beat it.
- Partial-window results around `.789-.790` are promising but depend on ffopportunity/NGS-era coverage.
- Same-season/future leakage remains blocked and was not used.

Review-only ranking simulation remains blocked until a separate readiness gate proves that a candidate is stable enough across comparable history and has appropriate source/use-gate clearance.
""",
    )
    write_md(
        OUT_DIR / "NEXT_DATA_OR_MODEL_LANE_RECOMMENDATION.md",
        """
# Next Data Or Model Lane Recommendation

Recommended next single lane: `Historical Market / ADP Source Gate and Data Mart Join V1`.

Rationale:

- More same-ingredient formula work is not the best next step.
- Snap/depth produced the best broad-window result, but not enough to justify ranking simulation.
- Partial-window modern ingredient combos are promising but not comparable to full history.
- Market/ADP remains a high-value candidate signal if historical/as-of safety can be proven.

The next lane should only verify historical/as-of safety, source gates, join feasibility, and review-only sidecar value. It must not run production ranking integration.
""",
    )
    write_md(
        OUT_DIR / "SCOREBOARD_NORMALIZATION_BLOCKERS_AND_CAVEATS.md",
        """
# Scoreboard Normalization Blockers And Caveats

- Full-history, broad-window, and partial-window scoreboards must remain separate.
- Partial ffopportunity/NGS-era results cannot be used to claim the `.755` full-history plateau was broken.
- Snap/depth `.763` is broad-window, not full `2013-2025`.
- Injury/availability `.757` is not material enough to change gates and did not beat snap/depth `.763`.
- PFR RB broken tackle remains descriptive only after failing same-row PYF comparison.
- Production/model-use, rankings integration, app/runtime changes, source promotion, push/merge, SportsDataIO, paid/API/free-trial/API-key work, PFF Elusive Rating, `nwr_elusive_proxy_review_only`, current-only ADP as historical feature, and same-season/future leakage remain blocked.
""",
    )
    write_md(
        OUT_DIR / "SCOREBOARD_NORMALIZATION_SOURCE_TRACE.md",
        "\n".join(
            [
                "# Scoreboard Normalization Source Trace",
                "",
                f"- Remote HQ verified: `{REMOTE_HEAD}`",
                f"- Latest injury availability commit verified: `{INJURY_COMMIT}`",
                f"- Handoff packet: `{HANDOFF_DIR}`",
                "- Read first: `LATEST_INJURY_AVAILABILITY_SUMMARY.md`",
                "- Inspected included result zip: `input_results/nwr_point_in_time_injury_availability_data_mart_gate_v1_results_20260709_168969c.zip`",
                "- Source result CSVs:",
                f"  - `{REPO / 'docs/hq/model/nwr_autonomous_ingredient_upgrade_sequence_v2_20260709/AUTONOMOUS_ALL_RESULTS_REQUIRED_SCHEMA.csv'}`",
                f"  - `{REPO / 'docs/hq/model/nflverse_epa_opportunity_formula_mart_sidecar_v1_20260709/NFLVERSE_EPA_OPPORTUNITY_ALL_RESULTS_REQUIRED_SCHEMA.csv'}`",
                f"  - `{REPO / 'docs/hq/model/nflverse_receiving_opportunity_formula_mart_sidecar_v1_20260709/NFLVERSE_RECEIVING_OPPORTUNITY_ALL_RESULTS_REQUIRED_SCHEMA.csv'}`",
                f"  - `{REPO / 'docs/hq/model/nflverse_snap_depth_role_formula_mart_sidecar_v1_20260709/NFLVERSE_SNAP_DEPTH_ROLE_ALL_RESULTS_REQUIRED_SCHEMA.csv'}`",
                f"  - `{REPO / 'docs/hq/model/point_in_time_injury_availability_data_mart_gate_v1_20260709/POINT_IN_TIME_INJURY_AVAILABILITY_ALL_RESULTS_REQUIRED_SCHEMA.csv'}`",
                "- PFR RB broken tackle and nflverse advanced audit statuses are carried from `CURRENT_ACCEPTED_STATUS_LEDGER_V2.csv` and accepted lane summaries.",
            ]
        ),
    )


def main() -> None:
    all_rows = load_scored_rows()
    full = top_n([r for r in all_rows if r["scoreboard_type"] == "full_history"], 40)
    broad = top_n([r for r in all_rows if r["scoreboard_type"] == "broad_window"], 40)
    partial = top_n([r for r in all_rows if r["scoreboard_type"] == "partial_window"], 40)
    best_rows = candidate_summary(full, broad, partial)
    write_csv(OUT_DIR / "INGREDIENT_SCOREBOARD_FULL_HISTORY_RESULTS.csv", full, SCOREBOARD_FIELDS)
    write_csv(OUT_DIR / "INGREDIENT_SCOREBOARD_BROAD_WINDOW_RESULTS.csv", broad, SCOREBOARD_FIELDS)
    write_csv(OUT_DIR / "INGREDIENT_SCOREBOARD_PARTIAL_WINDOW_RESULTS.csv", partial, SCOREBOARD_FIELDS)
    write_csv(OUT_DIR / "INGREDIENT_BEST_CANDIDATE_BY_SCOREBOARD.csv", best_rows)
    write_csv(OUT_DIR / "INGREDIENT_SAME_ROW_BASELINE_COMPARISON.csv", same_row_baseline_rows(all_rows))
    write_csv(OUT_DIR / "INGREDIENT_STATUS_AND_NEXT_USE_DECISION.csv", status_rows())
    make_reports(full, broad, partial, best_rows)
    print(
        {
            "full_rows": len(full),
            "broad_rows": len(broad),
            "partial_rows": len(partial),
            "best_full": best(full)["candidate_id"] if best(full) else "",
            "best_broad": best(broad)["candidate_id"] if best(broad) else "",
            "best_partial": best(partial)["candidate_id"] if best(partial) else "",
        }
    )


if __name__ == "__main__":
    main()
