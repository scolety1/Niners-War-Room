from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent

EXACT_REBUILD_DIR = Path(
    r"C:\NWR\Niners-War-Room-current-board-deterministic-rebuild-with-recovery-inputs-v1-20260708"
    r"\docs\hq\model\current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708"
)
FORMULA_DOC_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-formula-documentation-cleanup-v1-20260708"
    r"\docs\hq\model\model_v4_formula_documentation_cleanup_v1_20260708"
)
REPLAY_SUBSTRATE_DIR = Path(
    r"C:\NWR\Niners-War-Room-historical-model-v4-replay-substrate-v1-20260708"
    r"\docs\hq\model\historical_model_v4_replay_substrate_v1_20260708"
)
BACKTEST_DIR = Path(
    r"C:\NWR\Niners-War-Room-production-rankings-backtest-v1-20260708"
    r"\docs\hq\model\production_rankings_backtest_v1_20260708"
)
HUMAN_REVIEW_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-production-active-human-review-packet-v1-20260708"
    r"\docs\hq\model\model_v4_production_active_human_review_packet_v1_20260708"
)
LABEL_PACKET_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-formula-app-label-correction-packet-v1-20260708"
    r"\docs\hq\model\model_v4_formula_app_label_correction_packet_v1_20260708"
)
APP_LABEL_DIR = Path(
    r"C:\NWR\Niners-War-Room-model-v4-app-visible-label-correction-v1-20260708"
    r"\docs\hq\model\model_v4_app_visible_label_correction_v1_20260708"
)

SOURCE_MAP_PATH = REPLAY_SUBSTRATE_DIR / "MODEL_V4_FORMULA_COMPONENT_SOURCE_MAP.csv"
AVAILABILITY_MATRIX_PATH = (
    REPLAY_SUBSTRATE_DIR / "MODEL_V4_HISTORICAL_REPLAY_AVAILABILITY_MATRIX.csv"
)
PARTIAL_PANEL_PATH = (
    REPLAY_SUBSTRATE_DIR / "MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
)
CURRENT_RECEIPT_CHAIN_PATH = EXACT_REBUILD_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_RECEIPT_CHAIN.csv"
CURRENT_INPUT_MAP_PATH = EXACT_REBUILD_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_INPUT_MAP.csv"

CURRENT_COMPONENT_RECEIPT = {
    "nwr_dynasty_score": "reconciled_exact_current_board",
    "nwr_rank": "derived_from_reconciled_current_score",
    "checkpoint_review_score": "reconciled_current_checkpoint",
    "position_specific_review_score": "observed_current_component_rows",
    "review_scoring_points": "observed_current_component_rows",
    "positive_vorp_points": "observed_current_component_rows",
    "imported_rushing_first_downs": "observed_current_component_rows",
    "imported_receiving_first_downs": "observed_current_component_rows",
    "imported_first_down_points": "observed_current_component_rows",
    "return_scoring_points": "observed_current_component_rows",
    "lifecycle_modifier_review": "observed_current_lifecycle_rows",
    "confidence_cap": "observed_current_checkpoint",
    "wr_qb_v2_candidate_adjustment": "recomputed_exact_current_candidate_logic",
    "candidate_reason_codes": "recomputed_exact_current_candidate_logic",
    "candidate_evidence_fields_used": "recomputed_exact_current_candidate_logic",
    "old_pocket_qb_horizon_cap": "recomputed_exact_current_candidate_logic",
}

HISTORICAL_EQUIVALENTS = {
    "review_scoring_points": "prior_nwr_points; prior_nwr_ppg; prior_games",
    "imported_rushing_first_downs": "prior_rushing_first_downs",
    "imported_receiving_first_downs": "prior_receiving_first_downs",
    "imported_first_down_points": (
        "prior_rushing_first_downs; prior_receiving_first_downs; "
        "prior_passing_first_downs"
    ),
    "vorp_anchor": "prior_nwr_points; prior_nwr_ppg",
    "role_volume": (
        "prior_carries; prior_targets; prior_receptions; prior_touches; "
        "prior_opportunities"
    ),
    "first_down_high_value": (
        "prior_rushing_first_downs; prior_receiving_first_downs; "
        "prior_rushing_yards; prior_receiving_yards"
    ),
    "receiving_utility": "prior_targets; prior_receptions; prior_receiving_yards",
    "target_route_role": (
        "prior_targets; prior_receptions; prior_receiving_yards; "
        "prior_receiving_air_yards; prior_receiving_yards_after_catch"
    ),
    "first_down_yardage": (
        "prior_rushing_first_downs; prior_receiving_first_downs; "
        "prior_rushing_yards; prior_receiving_yards"
    ),
    "air_yard_role": "prior_receiving_air_yards; prior_receiving_yards_after_catch",
    "rushing_separation": "prior_carries; prior_rushing_yards; prior_rushing_first_downs",
    "passing_volume_security": (
        "prior_passing_attempts; prior_passing_completions; prior_passing_yards; "
        "prior_passing_first_downs"
    ),
    "passing_production": (
        "prior_passing_yards; prior_passing_td; prior_interceptions; "
        "prior_passing_first_downs"
    ),
    "route_target_role": (
        "prior_targets; prior_receptions; prior_receiving_yards; "
        "prior_receiving_air_yards; prior_receiving_yards_after_catch"
    ),
}

COMPONENT_PROXY_COLUMNS = {
    ("ALL", "review_scoring_points"): ["prior_nwr_points", "prior_nwr_ppg", "prior_games"],
    ("ALL", "imported_rushing_first_downs"): ["prior_rushing_first_downs"],
    ("ALL", "imported_receiving_first_downs"): ["prior_receiving_first_downs"],
    (
        "ALL",
        "imported_first_down_points",
    ): [
        "prior_rushing_first_downs",
        "prior_receiving_first_downs",
        "prior_passing_first_downs",
    ],
    ("RB", "vorp_anchor"): ["prior_nwr_points", "prior_nwr_ppg"],
    (
        "RB",
        "role_volume",
    ): [
        "prior_carries",
        "prior_targets",
        "prior_receptions",
        "prior_touches",
        "prior_opportunities",
    ],
    (
        "RB",
        "first_down_high_value",
    ): [
        "prior_rushing_first_downs",
        "prior_receiving_first_downs",
        "prior_rushing_yards",
        "prior_receiving_yards",
    ],
    ("RB", "receiving_utility"): ["prior_targets", "prior_receptions", "prior_receiving_yards"],
    ("WR", "vorp_anchor"): ["prior_nwr_points", "prior_nwr_ppg"],
    (
        "WR",
        "target_route_role",
    ): [
        "prior_targets",
        "prior_receptions",
        "prior_receiving_yards",
        "prior_receiving_air_yards",
        "prior_receiving_yards_after_catch",
    ],
    (
        "WR",
        "first_down_yardage",
    ): [
        "prior_rushing_first_downs",
        "prior_receiving_first_downs",
        "prior_rushing_yards",
        "prior_receiving_yards",
    ],
    ("WR", "air_yard_role"): ["prior_receiving_air_yards", "prior_receiving_yards_after_catch"],
    ("QB", "vorp_anchor"): ["prior_nwr_points", "prior_nwr_ppg"],
    ("QB", "rushing_separation"): ["prior_carries", "prior_rushing_yards", "prior_rushing_first_downs"],
    (
        "QB",
        "passing_volume_security",
    ): [
        "prior_passing_attempts",
        "prior_passing_completions",
        "prior_passing_yards",
        "prior_passing_first_downs",
    ],
    (
        "QB",
        "passing_production",
    ): [
        "prior_passing_yards",
        "prior_passing_td",
        "prior_interceptions",
        "prior_passing_first_downs",
    ],
    ("TE", "vorp_anchor"): ["prior_nwr_points", "prior_nwr_ppg"],
    (
        "TE",
        "route_target_role",
    ): [
        "prior_targets",
        "prior_receptions",
        "prior_receiving_yards",
        "prior_receiving_air_yards",
        "prior_receiving_yards_after_catch",
    ],
    (
        "TE",
        "first_down_yardage",
    ): [
        "prior_rushing_first_downs",
        "prior_receiving_first_downs",
        "prior_rushing_yards",
        "prior_receiving_yards",
    ],
}

KNOWN_BLOCKERS = [
    (
        "1",
        "checkpoint_review_score exact historical rows missing",
        "No season-by-season `current_player_value_full_board_review_rows.csv` equivalent exists.",
        "Blocks exact `nwr_dynasty_score` and exact rank replay.",
    ),
    (
        "2",
        "position_specific_review_score component receipts missing",
        "Current component rows exist only for current board; historical normalized component scores/weights are absent.",
        "Blocks exact QB/RB/WR/TE component score replay.",
    ),
    (
        "3",
        "lifecycle, age, role archetype, confidence cap history missing",
        "Current lifecycle age adapter reproduced 2026 board, but historical age/role/confidence receipts are not available.",
        "Blocks exact checkpoint replay and old-pocket QB guardrail history.",
    ),
    (
        "4",
        "route/YPRR/TPRR/red-zone exact receipts missing",
        "Partial V3 panel has targets/yards/air-yard/YAC overlap but not true route denominators or exact current scoring transforms.",
        "Blocks exact WR/TE route role and efficiency components.",
    ),
    (
        "5",
        "return scoring and shadow sidecars missing",
        "`shadow_model_v2_metrics.csv` and historical return-scoring receipts remain absent.",
        "Blocks exact shadow/guardrail and return component replay if required.",
    ),
    (
        "6",
        "source admission remains review-only",
        "The current board remains candidate/review-only, and the partial panel is not model/training/source-truth approved.",
        "Blocks production accuracy claims and source promotion.",
    ),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def receipt_hash(*parts: object) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()


def positions_for_scope(scope: str) -> set[str]:
    if scope == "ALL":
        return {"QB", "RB", "WR", "TE"}
    return {part for part in scope.replace("K", "").split("/") if part in {"QB", "RB", "WR", "TE"}}


def source_columns_for(position: str, component: str) -> list[str]:
    return COMPONENT_PROXY_COLUMNS.get((position, component)) or COMPONENT_PROXY_COLUMNS.get(
        ("ALL", component), []
    )


def nonempty_count(row: dict[str, str], columns: list[str]) -> int:
    return sum(1 for col in columns if str(row.get(col, "")).strip() not in {"", "Not enough information"})


def build_target_list(source_map: list[dict[str, str]], receipt_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    current_receipts = {
        row["field_or_layer"]: row for row in receipt_rows if row.get("field_or_layer")
    }
    target_rows: list[dict[str, object]] = []
    for row in source_map:
        component = row["component_name"]
        replay_status = row["replay_status"]
        exact_possible = "No"
        partial_possible = "Yes" if replay_status == "PARTIAL_REPLAY_AVAILABLE" else "No"
        if replay_status == "EXCLUDED_FROM_REPLAY":
            backfill_status = "excluded_from_replay"
        elif replay_status == "PARTIAL_REPLAY_AVAILABLE":
            backfill_status = "backfilled_partial_replay_proxy_receipts"
        else:
            backfill_status = "exact_receipt_missing_blocked"
        current = current_receipts.get(component)
        current_status = (
            current["receipt_status"]
            if current
            else CURRENT_COMPONENT_RECEIPT.get(component, "current_surface_mapped_not_receipt_proven")
        )
        target_rows.append(
            {
                "component_name": component,
                "position_scope": row["position_scope"],
                "component_layer": row["component_layer"],
                "production_input": row["production_input"],
                "current_source_file_function": row["current_source_file_function"],
                "current_receipt_status": current_status,
                "current_receipt_source_path": current.get("source_path", "") if current else "",
                "current_source_column": current.get("source_column", "") if current else "",
                "required_historical_equivalent": HISTORICAL_EQUIVALENTS.get(
                    component, "exact season-by-season Model v4 component receipt required"
                ),
                "source_type": "historical_lagged_v3_proxy" if partial_possible == "Yes" else "exact_model_v4_required",
                "admission_status": row["admission_status"],
                "decision_date_safety": row["available_at_decision_date"],
                "identity_risk": row["identity_join_risk"],
                "leakage_risk": row["leakage_risk"],
                "historical_availability": row["historical_availability"],
                "missingness": row["caveat"],
                "can_backfill_now": partial_possible,
                "historical_receipt_backfill_status": backfill_status,
                "exact_replay_status": "blocked" if exact_possible == "No" else "ready",
                "partial_replay_status": "partial_ready" if partial_possible == "Yes" else "not_available",
                "caveat": row["drop_proxy_block"] or row["caveat"],
            }
        )
    return target_rows


def build_receipts(partial_panel: list[dict[str, str]], source_hash: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in partial_panel:
        position = item["position"]
        player_id = item["player_id_gsis"]
        player_name = item.get("target_player_name") or item.get("feature_player_name", "")
        components = [
            "review_scoring_points",
            "imported_rushing_first_downs",
            "imported_receiving_first_downs",
            "imported_first_down_points",
        ]
        position_components = {
            "QB": ["vorp_anchor", "rushing_separation", "passing_volume_security", "passing_production"],
            "RB": ["vorp_anchor", "role_volume", "first_down_high_value", "receiving_utility"],
            "WR": ["vorp_anchor", "target_route_role", "first_down_yardage", "air_yard_role"],
            "TE": ["vorp_anchor", "route_target_role", "first_down_yardage"],
        }
        components.extend(position_components.get(position, []))
        for component in components:
            columns = source_columns_for(position, component)
            observed = nonempty_count(item, columns)
            if not columns:
                continue
            missingness = "source_columns_all_empty" if observed == 0 else "source_columns_present"
            if item.get("optional_source_null_fenced") == "True":
                missingness += "; optional_null_fenced"
            rows.append(
                {
                    "target_season": item["target_season"],
                    "feature_season": item["feature_season"],
                    "position": position,
                    "player_id": player_id,
                    "player_name": player_name,
                    "component_name": component,
                    "historical_component_status": "partial_replay_proxy_only",
                    "historical_source_artifact": (
                        "MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
                    ),
                    "source_receipt_pointer": "v3_source_semantics_substrate_parquet",
                    "source_columns": "|".join(columns),
                    "source_columns_nonempty_count": observed,
                    "source_hash": source_hash,
                    "source_gate_status": "review_only_not_model_training_prod",
                    "decision_date_safe_flag": (
                        "partial_v3_lagged_safe"
                        if item.get("leakage_check_result", "").startswith("PASS")
                        and item.get("asof_check_result", "").startswith("PASS")
                        else "blocked"
                    ),
                    "identity_caveat_flag": (
                        "player_id_gsis_present" if player_id else "identity_missing"
                    ),
                    "leakage_caveat_flag": "PASS_FEATURE_N_TARGET_N_PLUS_1;PASS_NO_TARGET_CONTEXT",
                    "missingness_flag": missingness,
                    "receipt_hash": receipt_hash(
                        item["substrate_row_id"], component, "|".join(columns), source_hash
                    ),
                    "replay_eligibility_flag": "partial_replay_only_not_exact_model_v4",
                    "exact_model_v4_replay_status": item.get("exact_model_v4_replay_status", ""),
                    "partial_replay_status": item.get("partial_replay_status", ""),
                    "caveat": "partial_proxy_not_exact_model_v4",
                }
            )
    return rows


def build_readiness_matrix(
    availability_rows: list[dict[str, str]], source_map: list[dict[str, str]], receipts: list[dict[str, object]]
) -> list[dict[str, object]]:
    receipt_counts: Counter[tuple[str, str, str]] = Counter()
    for receipt in receipts:
        receipt_counts[
            (str(receipt["target_season"]), str(receipt["position"]), str(receipt["component_name"]))
        ] += 1

    target_components_by_position: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_map:
        if not row["production_input"].startswith("Yes"):
            continue
        for position in positions_for_scope(row["position_scope"]):
            target_components_by_position[position].append(row)

    rows: list[dict[str, object]] = []
    for row in availability_rows:
        position = row["position"]
        season = row["target_season"]
        targets = target_components_by_position[position]
        required = len(targets)
        available_components = sorted(
            {
                component
                for (target_season, pos, component), count in receipt_counts.items()
                if target_season == season and pos == position and count > 0
            }
        )
        blocked = [
            target["component_name"]
            for target in targets
            if target["replay_status"] == "EXACT_REPLAY_BLOCKED"
        ]
        rows.append(
            {
                "target_season": season,
                "feature_season": row["feature_season"],
                "position": position,
                "required_components": required,
                "available_partial_receipt_components": len(available_components),
                "available_partial_receipt_component_names": "|".join(available_components),
                "blocked_components": len(blocked),
                "blocked_component_names": "|".join(blocked),
                "label_coverage": row["label_coverage"],
                "identity_coverage": row["identity_coverage"],
                "decision_date_safe_coverage": row["decision_date_safe"],
                "exact_source_receipt_coverage": row["exact_source_receipt_coverage"],
                "partial_input_overlap_coverage": row["partial_input_overlap_coverage"],
                "replay_row_can_exist": row["valid_partial_replay_row_can_exist"],
                "exact_replay_possible": row["valid_exact_replay_row_can_exist"],
                "partial_replay_possible": row["valid_partial_replay_row_can_exist"],
                "replay_status": (
                    "partial_replay_ready_exact_blocked"
                    if row["valid_partial_replay_row_can_exist"] == "Yes"
                    else "blocked"
                ),
                "main_blocker": row["main_blocker"],
            }
        )
    return rows


def build_coverage_summary(receipts: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in receipts:
        grouped[str(row["component_name"])].append(row)
    rows: list[dict[str, object]] = []
    for component, items in sorted(grouped.items()):
        players = {item["player_id"] for item in items}
        seasons = {item["target_season"] for item in items}
        positions = {item["position"] for item in items}
        nonempty = sum(1 for item in items if int(item["source_columns_nonempty_count"]) > 0)
        rows.append(
            {
                "component_name": component,
                "receipt_rows": len(items),
                "unique_players": len(players),
                "target_season_min": min(seasons),
                "target_season_max": max(seasons),
                "target_season_count": len(seasons),
                "positions": "|".join(sorted(positions)),
                "rows_with_nonempty_source_columns": nonempty,
                "nonempty_source_column_rate": round(nonempty / len(items), 6) if items else 0,
                "historical_backfill_status": "partial_replay_proxy_only",
                "exact_model_v4_replay_status": "blocked",
                "caveat": "Receipts prove lagged factual source availability only, not exact Model v4 component scores.",
            }
        )
    return rows


def write_markdown(
    target_rows: list[dict[str, object]],
    receipts: list[dict[str, object]],
    readiness_rows: list[dict[str, object]],
    coverage_rows: list[dict[str, object]],
    source_hash: str,
) -> None:
    partial_components = sum(1 for row in target_rows if row["can_backfill_now"] == "Yes")
    blocked_components = sum(
        1 for row in target_rows if row["historical_receipt_backfill_status"] == "exact_receipt_missing_blocked"
    )
    excluded_components = sum(
        1 for row in target_rows if row["historical_receipt_backfill_status"] == "excluded_from_replay"
    )
    exact_ready = sum(1 for row in readiness_rows if row["exact_replay_possible"] == "Yes")
    partial_ready = sum(1 for row in readiness_rows if row["partial_replay_possible"] == "Yes")
    position_summary = Counter(str(row["position"]) for row in receipts)
    readiness_by_position: dict[str, dict[str, object]] = {}
    for row in readiness_rows:
        position = str(row["position"])
        if position not in readiness_by_position:
            readiness_by_position[position] = {
                "required": row["required_components"],
                "available": row["available_partial_receipt_components"],
                "blocked": row["blocked_components"],
                "blocker": row["main_blocker"],
            }
    readiness_lines = []
    for position in ["QB", "RB", "WR", "TE"]:
        row = readiness_by_position[position]
        readiness_lines.append(
            "| 2013-2025 | {position} | {required} | {available} | {blocked} | "
            "partial replay possible; exact blocked | {blocker} |".format(
                position=position,
                required=row["required"],
                available=row["available"],
                blocked=row["blocked"],
                blocker=row["blocker"],
            )
        )

    report = f"""# Model v4 Historical Component Receipt Backfill V1 Report

## Verdict

`YELLOW_MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS_PARTIAL_WITH_BLOCKERS`

## Clear Answer

Exact Model v4 historical replay is not now possible because the exact season-by-season checkpoint, lifecycle, confidence, candidate-overlay, and normalized component receipt chain still does not exist. This lane backfilled `{len(receipts)}` review-only historical partial receipts from the existing lagged V3 factual overlap panel, but those receipts are proxy/source-availability receipts only and must not be treated as exact Model v4 scores.

## What Was Backfilled

- Current component targets reviewed: `{len(target_rows)}`.
- Components with partial historical receipt analogs: `{partial_components}`.
- Components still exact-replay blocked: `{blocked_components}`.
- Components excluded from replay: `{excluded_components}`.
- Review-only player/component receipt rows backfilled: `{len(receipts)}`.
- Historical panel source SHA256: `{source_hash}`.
- Season coverage: `2013-2025`.
- Position receipt rows: `{dict(sorted(position_summary.items()))}`.

## Historical Replay Readiness

| Season Range | Position | Required Components | Available | Blocked | Replay Status | Main Blocker |
| ------------ | -------- | ------------------: | --------: | ------: | ------------- | ------------ |
{chr(10).join(readiness_lines)}

## Component Receipt Coverage

See `MODEL_V4_HISTORICAL_RECEIPT_COVERAGE_SUMMARY.csv`.

## Known Blockers

See `MODEL_V4_HISTORICAL_COMPONENT_BLOCKERS.md`.

## Benchmark Contract

See `MODEL_V4_NEXT_REPLAY_BENCHMARK_CONTRACT.md`. The next benchmark can only be a partial historical replay benchmark unless exact Model v4 historical receipts are recovered first.

## Production Status

- Current board remains review-only.
- Exact current-board rebuild remains verified.
- Production-active status remains blocked.
- Historical accuracy remains unproven until a separate benchmark is run.
- No source was promoted by this lane.
- No ranking output, model weight, app behavior, or canonical `local_exports` file was changed.

## Recommended Next Lane

`Partial historical replay benchmark`

This should benchmark only the partial lagged receipt panel against baselines and must state that it is not exact Model v4 replay. Exact replay still requires additional historical source/receipt recovery.
"""
    (OUT_DIR / "MODEL_V4_HISTORICAL_COMPONENT_RECEIPT_BACKFILL_V1_REPORT.md").write_text(
        report, encoding="utf-8"
    )

    blockers = ["# Model v4 Historical Component Blockers", "", "## Ranked Blockers", ""]
    for rank, title, evidence, impact in KNOWN_BLOCKERS:
        blockers.extend([f"{rank}. **{title}**", f"   - Evidence: {evidence}", f"   - Impact: {impact}", ""])
    blockers.extend(
        [
            "## Cold-Water Accuracy Caveat",
            "",
            "Production Rankings Backtest V1 found useful signal, but the current-formula-family proxy did not beat simple prior-year finish overall. This lane does not change that evidence and does not claim production accuracy.",
            "",
            "## Shadow / Sidecar Caveats",
            "",
            "- `shadow_model_v2_metrics.csv` remains missing for exact shadow/guardrail historical replay if required.",
            "- The exact original `veteran_player_inputs.csv` age sidecar remains absent.",
            "- The current-board age adapter reproduced the current board exactly, but this does not prove historical age/lifecycle validity.",
        ]
    )
    (OUT_DIR / "MODEL_V4_HISTORICAL_COMPONENT_BLOCKERS.md").write_text(
        "\n".join(blockers) + "\n", encoding="utf-8"
    )

    source_trace = f"""# Model v4 Historical Receipt Source Trace

## Primary Sources

| Source | Path | Use |
| --- | --- | --- |
| Exact current-board rebuild packet | `{EXACT_REBUILD_DIR}` | Current receipt chain and exact current-board proof. |
| Formula documentation / cleanup packet | `{FORMULA_DOC_DIR}` | Current component registry and replay blockers. |
| Historical Model v4 replay substrate | `{REPLAY_SUBSTRATE_DIR}` | Component source map, partial replay panel, and availability matrix. |
| Production Rankings Backtest V1 | `{BACKTEST_DIR}` | Accuracy caveat and prior-year baseline comparison context. |
| Model v4 human review packet | `{HUMAN_REVIEW_DIR}` | Production-active consideration caveats. |
| Label correction packet | `{LABEL_PACKET_DIR}` | Canonical board label/status taxonomy. |
| App-visible label implementation | `{APP_LABEL_DIR}` | Confirmed current app label is display-only and review-safe. |

## Historical Panel

- Panel: `{PARTIAL_PANEL_PATH}`
- Receipt CSV source alias: `MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv`
- Receipt pointer alias: `v3_source_semantics_substrate_parquet`
- Receipt pointer full path: `docs/hq/experiments/historical_tuning_substrate_expansion_v3_source_semantics_audit_20260701/nwr_historical_tuning_feature_target_substrate_v3.parquet`
- SHA256: `{source_hash}`
- Rows: `5518`
- Status: `review_only=true`, `model_use_allowed=false`, `training_allowed=false`, `production_approved=false`

## Source Limits

The backfilled receipts trace lagged factual V3 overlap only. They do not contain exact Model v4 normalized scores, weights, checkpoint outputs, lifecycle modifiers, confidence caps, WR/QB v2 candidate overlays, or production-active approvals.
"""
    (OUT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_SOURCE_TRACE.md").write_text(
        source_trace, encoding="utf-8"
    )

    contract = f"""# Model v4 Next Replay Benchmark Contract

## Status

`PARTIAL_REPLAY_BENCHMARK_ALLOWED_EXACT_REPLAY_BLOCKED`

## Eligible Benchmark Type

The next benchmark may be a partial historical replay benchmark using only the review-only historical component receipts created in this lane. It must not be described as exact Model v4 replay.

## Seasons

- Target seasons: `2013-2025`
- Feature seasons: `2012-2024`
- Decision rule: target season `Y` may use only completed feature season `Y-1` factual inputs.

## Positions

- QB
- RB
- WR
- TE

## Eligible Universe

Only rows present in `MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS.csv` and the existing partial replay input panel are eligible. Rookie/no-prior-season rows are not complete in this substrate.

## Allowed Components

Allowed as partial proxy receipts only:

{chr(10).join(f'- `{row["component_name"]}`' for row in coverage_rows)}

## Blocked Components

Blocked for exact replay:

- `nwr_dynasty_score`
- `nwr_rank`
- `checkpoint_review_score`
- `position_specific_review_score`
- `positive_vorp_points`
- `return_scoring_points`
- `lifecycle_modifier_review`
- `confidence_cap`
- `discipline_multiplier`
- `wr_qb_v2_candidate_adjustment`
- `candidate_reason_codes`
- `candidate_evidence_fields_used`
- `old_pocket_qb_horizon_cap`
- exact route/YPRR/TPRR/red-zone normalized components where true denominators are absent

## Labels

Use held-out target-season labels only:

- `next_nwr_points`
- `next_nwr_ppg`
- `next_position_finish`
- `startable_hit`
- `startable_bucket`

## Metrics

Report at minimum:

- MAE
- RMSE
- Spearman
- Top-12 / Top-24 / Top-36 hit rates where position-applicable
- Startable precision and recall
- Coverage by season and position
- Baseline comparisons against prior-year finish and current-formula-family proxy

## Leakage Checks

- Confirm every feature row uses `feature_season = target_season - 1`.
- Confirm every receipt remains `review_only` and `partial_replay_proxy_only`.
- Confirm no current roster, injury, market, ADP, projection, ranking, target-season, or current-board artifact field is used as a historical input.
- Confirm missing/null-fenced source columns are not imputed as exact zero unless source semantics separately prove explicit zero.

## Caveats

- This benchmark cannot claim production accuracy.
- This benchmark cannot promote sources.
- This benchmark cannot tune or activate production rankings.
- Exact Model v4 replay remains blocked until exact historical component receipts exist.
"""
    (OUT_DIR / "MODEL_V4_NEXT_REPLAY_BENCHMARK_CONTRACT.md").write_text(
        contract, encoding="utf-8"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source_map = read_csv(SOURCE_MAP_PATH)
    availability_rows = read_csv(AVAILABILITY_MATRIX_PATH)
    receipt_chain = read_csv(CURRENT_RECEIPT_CHAIN_PATH)
    partial_panel = read_csv(PARTIAL_PANEL_PATH)
    source_hash = sha256_file(PARTIAL_PANEL_PATH)

    target_rows = build_target_list(source_map, receipt_chain)
    receipt_rows = build_receipts(partial_panel, source_hash)
    readiness_rows = build_readiness_matrix(availability_rows, source_map, receipt_rows)
    coverage_rows = build_coverage_summary(receipt_rows)

    write_csv(
        OUT_DIR / "MODEL_V4_HISTORICAL_COMPONENT_TARGET_LIST.csv",
        target_rows,
        [
            "component_name",
            "position_scope",
            "component_layer",
            "production_input",
            "current_source_file_function",
            "current_receipt_status",
            "current_receipt_source_path",
            "current_source_column",
            "required_historical_equivalent",
            "source_type",
            "admission_status",
            "decision_date_safety",
            "identity_risk",
            "leakage_risk",
            "historical_availability",
            "missingness",
            "can_backfill_now",
            "historical_receipt_backfill_status",
            "exact_replay_status",
            "partial_replay_status",
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS.csv",
        receipt_rows,
        [
            "target_season",
            "feature_season",
            "position",
            "player_id",
            "player_name",
            "component_name",
            "historical_component_status",
            "historical_source_artifact",
            "source_receipt_pointer",
            "source_columns",
            "source_columns_nonempty_count",
            "source_hash",
            "source_gate_status",
            "decision_date_safe_flag",
            "identity_caveat_flag",
            "leakage_caveat_flag",
            "missingness_flag",
            "receipt_hash",
            "replay_eligibility_flag",
            "exact_model_v4_replay_status",
            "partial_replay_status",
            "caveat",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_HISTORICAL_REPLAY_READINESS_MATRIX.csv",
        readiness_rows,
        [
            "target_season",
            "feature_season",
            "position",
            "required_components",
            "available_partial_receipt_components",
            "available_partial_receipt_component_names",
            "blocked_components",
            "blocked_component_names",
            "label_coverage",
            "identity_coverage",
            "decision_date_safe_coverage",
            "exact_source_receipt_coverage",
            "partial_input_overlap_coverage",
            "replay_row_can_exist",
            "exact_replay_possible",
            "partial_replay_possible",
            "replay_status",
            "main_blocker",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_HISTORICAL_RECEIPT_COVERAGE_SUMMARY.csv",
        coverage_rows,
        [
            "component_name",
            "receipt_rows",
            "unique_players",
            "target_season_min",
            "target_season_max",
            "target_season_count",
            "positions",
            "rows_with_nonempty_source_columns",
            "nonempty_source_column_rate",
            "historical_backfill_status",
            "exact_model_v4_replay_status",
            "caveat",
        ],
    )
    write_markdown(target_rows, receipt_rows, readiness_rows, coverage_rows, source_hash)

    print(f"target_components={len(target_rows)}")
    print(f"partial_receipts={len(receipt_rows)}")
    print(f"readiness_rows={len(readiness_rows)}")
    print(f"coverage_rows={len(coverage_rows)}")
    print(f"partial_panel_sha256={source_hash}")


if __name__ == "__main__":
    main()
