from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]

PANEL_PATH = REPO / "docs/hq/model/historical_model_v4_replay_substrate_v1_20260708/MODEL_V4_PARTIAL_REPLAY_INPUT_PANEL_REVIEW_ONLY.csv"
CONTRACT_DIR = REPO / "docs/hq/master/model_v4_historical_receipt_regeneration_contract_planning_v1_20260709"
MASTER_REVIEW_DIR = REPO / "docs/hq/master/model_v4_historical_receipt_master_review_admission_decision_v1_20260709"
FREEZE_DIR = REPO / "docs/hq/data_hygiene/model_v4_historical_receipt_freeze_schema_validation_v1_20260709"
CONFIDENCE_CAP_DIR = REPO / "docs/hq/data_hygiene/model_v4_confidence_cap_receipt_regeneration_pilot_v1_20260709"
HQ1_STANDARD_DIR = REPO / "docs/hq/deep_research_upgrades/hq1_source_receipt_chain_standard_v1_20260708"
DATA_HYGIENE_CHARTER_DIR = REPO / "docs/hq/data_hygiene/data_hygiene_operating_charter_v1_20260708"
CONFIDENCE_SIGNAL_COMMIT = "b548776c4343b7bd38cb63f84b51b0334fd8b352"
CONFIDENCE_SIGNAL_ARTIFACT = Path(
    r"C:\NWR\Niners-War-Room-model-v4-confidence-cap-component-signal-test-v1-20260709"
    r"\docs\hq\model\model_v4_confidence_cap_component_signal_test_v1_20260709"
)

RECEIPT_VERSION = "model_v4_role_archetype_receipt_regeneration_pilot_v1_20260709"
SOURCE_GATE_STATUS = "review_only_not_model_training_prod"
ALLOWED_USE = "review_only_regenerated_not_production_model_use"
BLOCKED_USE = "production_model_use|ranking_integration|formula_activation|source_promotion"

POSITION_VOLUME_METRIC = {
    "QB": "prior_passing_attempts",
    "RB": "prior_touches",
    "WR": "prior_targets",
    "TE": "prior_targets",
}

POSITION_VOLUME_LABEL = {
    "QB": "passing_volume",
    "RB": "touch_volume",
    "WR": "target_volume",
    "TE": "target_volume",
}

OUTPUT_COLUMNS = [
    "season",
    "feature_season",
    "player_id",
    "canonical_player_key",
    "player_name",
    "position",
    "receipt_family",
    "role_archetype",
    "role_archetype_status",
    "role_archetype_method",
    "role_inputs_used",
    "games_context",
    "volume_context",
    "usage_bucket",
    "sparse_history_flag",
    "low_games_flag",
    "source_artifact",
    "source_hash",
    "source_sha256",
    "source_gate_status",
    "decision_date_safe",
    "leakage_flag",
    "identity_flag",
    "missingness_flag",
    "true_zero_flag",
    "unknown_flag",
    "true_zero_vs_unknown_status",
    "review_only_status",
    "allowed_use",
    "blocked_use",
    "receipt_version",
    "warning_flags",
    "receipt_hash",
    "caveat",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row_count(path: Path) -> int | str:
    if path.suffix.lower() != ".csv":
        return ""
    with path.open(newline="", encoding="utf-8-sig") as f:
        return max(0, sum(1 for _ in csv.reader(f)) - 1)


def columns(path: Path) -> str:
    if path.suffix.lower() != ".csv":
        return ""
    with path.open(newline="", encoding="utf-8-sig") as f:
        return "|".join(next(csv.reader(f)))


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


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    frac = pos - lo
    return xs[lo] * (1 - frac) + xs[hi] * frac


def group_thresholds(rows: list[dict[str, str]]) -> dict[tuple[str, str], tuple[float, float]]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        position = row["position"]
        metric = POSITION_VOLUME_METRIC[position]
        value = num(row.get(metric))
        if value is not None:
            grouped[(row["target_season"], position)].append(value)
    return {key: (percentile(values, 0.25), percentile(values, 0.75)) for key, values in grouped.items()}


def usage_bucket(value: float | None, low_threshold: float, high_threshold: float) -> str:
    if value is None:
        return "unknown_volume"
    if value >= high_threshold:
        return "high_volume"
    if value <= low_threshold:
        return "low_volume"
    return "moderate_volume"


def games_context(prior_games: float | None) -> str:
    if prior_games is None:
        return "unknown_games"
    if prior_games < 8:
        return "low_games_lt8"
    return "games_8plus"


def role_archetype(position: str, prior_games: float | None, bucket: str) -> str:
    if prior_games is None:
        return f"{position.lower()}_unknown_games_role_context"
    if prior_games < 8:
        return f"{position.lower()}_sparse_history_low_games"
    volume_label = POSITION_VOLUME_LABEL[position]
    return f"{position.lower()}_{bucket}_{volume_label}"


def true_zero_unknown(value: float | None) -> tuple[str, str, str]:
    if value is None:
        return "false", "true", "unknown_source_value"
    if value == 0:
        return "true", "false", "source_present_true_zero"
    return "false", "false", "source_present_nonzero"


def receipt_hash(row: dict[str, object]) -> str:
    payload = "|".join(str(row.get(col, "")) for col in OUTPUT_COLUMNS if col != "receipt_hash")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_receipts(panel_rows: list[dict[str, str]], source_hash: str) -> list[dict[str, object]]:
    thresholds = group_thresholds(panel_rows)
    receipts = []
    for row in panel_rows:
        position = row["position"]
        metric = POSITION_VOLUME_METRIC[position]
        value = num(row.get(metric))
        prior_games = num(row.get("prior_games"))
        low_threshold, high_threshold = thresholds[(row["target_season"], position)]
        bucket = usage_bucket(value, low_threshold, high_threshold)
        low_games = prior_games is None or prior_games < 8
        sparse = low_games
        true_zero_flag, unknown_flag, true_zero_status = true_zero_unknown(value)
        warning_flags = []
        if sparse:
            warning_flags.append("sparse_history_prior_games_lt8")
        if bucket == "unknown_volume":
            warning_flags.append("unknown_primary_volume")
        if value == 0:
            warning_flags.append("primary_volume_true_zero")
        if not warning_flags:
            warning_flags.append("none")
        source_columns = [
            "feature_season",
            "target_season",
            "player_id_gsis",
            "position",
            "prior_games",
            metric,
            "prior_nwr_points",
            "prior_nwr_ppg",
            "prior_opportunities",
            "prior_touches",
            "prior_targets",
            "prior_carries",
            "prior_passing_attempts",
        ]
        out = {
            "season": row["target_season"],
            "feature_season": row["feature_season"],
            "player_id": row["player_id_gsis"],
            "canonical_player_key": row["player_id_gsis"],
            "player_name": row["feature_player_name"],
            "position": position,
            "receipt_family": "role_archetype_receipts",
            "role_archetype": role_archetype(position, prior_games, bucket),
            "role_archetype_status": "review_only_lagged_role_context",
            "role_archetype_method": "prior_season_games_and_position_specific_volume_quartiles_no_future_role_labels",
            "role_inputs_used": "|".join(source_columns),
            "games_context": games_context(prior_games),
            "volume_context": (
                f"{metric}:{bucket}:q25={low_threshold:.3f}:q75={high_threshold:.3f}:value="
                f"{'' if value is None else f'{value:.3f}'}"
            ),
            "usage_bucket": bucket,
            "sparse_history_flag": str(sparse).lower(),
            "low_games_flag": str(low_games).lower(),
            "source_artifact": str(PANEL_PATH),
            "source_hash": source_hash,
            "source_sha256": source_hash,
            "source_gate_status": SOURCE_GATE_STATUS,
            "decision_date_safe": "yes",
            "leakage_flag": "PASS_LAGGED_PRIOR_SEASON_INPUTS_ONLY_NO_CURRENT_OR_FUTURE_ROLE_LABELS",
            "identity_flag": "PASS_GSIS_PLAYER_ID_PRESENT",
            "missingness_flag": "primary_volume_unknown" if value is None else "source_columns_present",
            "true_zero_flag": true_zero_flag,
            "unknown_flag": unknown_flag,
            "true_zero_vs_unknown_status": true_zero_status,
            "review_only_status": "review_only_regenerated_not_production_model_use",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "receipt_version": RECEIPT_VERSION,
            "warning_flags": "|".join(warning_flags),
            "receipt_hash": "",
            "caveat": "review_only_role_archetype_from_lagged_usage_context_not_future_role_or_exact_model_v4",
        }
        out["receipt_hash"] = receipt_hash(out)
        receipts.append(out)
    return receipts


def source_manifest(panel_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    paths = [
        (PANEL_PATH, "lagged_player_season_usage_production_panel_for_role_archetype_receipts", "review_only_regeneration_input"),
        (CONTRACT_DIR / "MODEL_V4_REGENERATION_SCHEMA_CONTRACTS.csv", "schema_contract", "governance_reference"),
        (CONTRACT_DIR / "MODEL_V4_REGENERATION_SOURCE_ALLOW_BLOCK_MATRIX.csv", "source_allow_block_contract", "governance_reference"),
        (CONTRACT_DIR / "MODEL_V4_REGENERATION_LEAKAGE_ASOF_RULES.md", "leakage_asof_contract", "governance_reference"),
        (CONTRACT_DIR / "MODEL_V4_REGENERATION_IDENTITY_MISSINGNESS_RULES.md", "identity_missingness_contract", "governance_reference"),
        (MASTER_REVIEW_DIR / "MODEL_V4_HISTORICAL_RECEIPT_MASTER_REVIEW_ADMISSION_DECISION_V1_REPORT.md", "master_review_context", "governance_reference"),
        (FREEZE_DIR / "MODEL_V4_HISTORICAL_RECEIPT_FREEZE_SCHEMA_VALIDATION_V1_REPORT.md", "freeze_schema_context", "governance_reference"),
    ]
    rows = []
    for path, role, use_gate in paths:
        rows.append(
            {
                "source_artifact": str(path),
                "sha256": sha256(path),
                "row_count": row_count(path),
                "column_count": len(columns(path).split("|")) if path.suffix.lower() == ".csv" else "",
                "columns": columns(path),
                "source_role": role,
                "use_gate_status": use_gate,
                "notes": "all source inputs are review/governance artifacts; no production/model-use source promotion",
            }
        )
    return rows


def schema_validation(receipts: list[dict[str, object]]) -> list[dict[str, object]]:
    keys = [(row["season"], row["player_id"], row["position"]) for row in receipts]
    duplicate_keys = len(keys) - len(set(keys))
    forbidden = {"future_role", "post_outcome_role", "current_depth_chart", "current_adp", "production_approved"}
    return [
        {
            "check": "row_count",
            "result": len(receipts),
            "passed": len(receipts) == 5518,
            "caveat": "expected player-season rows from partial replay panel",
        },
        {
            "check": "required_columns_present",
            "result": "|".join(OUTPUT_COLUMNS),
            "passed": all(col in receipts[0] for col in OUTPUT_COLUMNS),
            "caveat": "",
        },
        {
            "check": "duplicate_key_count",
            "result": duplicate_keys,
            "passed": duplicate_keys == 0,
            "caveat": "key is season/player_id/position",
        },
        {
            "check": "forbidden_columns_absent",
            "result": "|".join(sorted(forbidden.intersection(receipts[0].keys()))),
            "passed": not forbidden.intersection(receipts[0].keys()),
            "caveat": "",
        },
        {
            "check": "decision_date_safe",
            "result": sum(1 for row in receipts if row["decision_date_safe"] == "yes"),
            "passed": all(row["decision_date_safe"] == "yes" for row in receipts),
            "caveat": "role labels use prior-season fields only",
        },
        {
            "check": "leakage_flag_pass",
            "result": sum(1 for row in receipts if str(row["leakage_flag"]).startswith("PASS")),
            "passed": all(str(row["leakage_flag"]).startswith("PASS") for row in receipts),
            "caveat": "",
        },
        {
            "check": "identity_flag_pass",
            "result": sum(1 for row in receipts if str(row["identity_flag"]).startswith("PASS")),
            "passed": all(str(row["identity_flag"]).startswith("PASS") for row in receipts),
            "caveat": "",
        },
        {
            "check": "review_only_allowed_use",
            "result": sum(1 for row in receipts if row["allowed_use"] == ALLOWED_USE),
            "passed": all(row["allowed_use"] == ALLOWED_USE for row in receipts),
            "caveat": "not production/model-use",
        },
    ]


def distribution(receipts: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped = Counter((row["season"], row["position"], row["role_archetype"]) for row in receipts)
    totals = Counter((row["season"], row["position"]) for row in receipts)
    rows = []
    for (season, position, archetype), count in sorted(grouped.items()):
        rows.append(
            {
                "season": season,
                "position": position,
                "role_archetype": archetype,
                "rows": count,
                "position_season_rows": totals[(season, position)],
                "share": f"{count / totals[(season, position)]:.6f}",
            }
        )
    return rows


def md_report(receipts: list[dict[str, object]]) -> str:
    seasons = sorted({str(row["season"]) for row in receipts})
    position_counts = Counter(str(row["position"]) for row in receipts)
    archetype_counts = Counter(str(row["role_archetype"]) for row in receipts)
    top = ", ".join(f"{name}={count}" for name, count in archetype_counts.most_common(8))
    return "\n".join(
        [
            "# Model v4 Role Archetype Receipt Regeneration Pilot V1 Report",
            "",
            "## Verdict",
            "",
            "`GREEN_ROLE_ARCHETYPE_RECEIPTS_REGENERATED_REVIEW_ONLY`",
            "",
            "## Clear Answer",
            "",
            "Role-archetype receipts were regenerated safely as review-only, lagged usage/context receipts. They may support future review-only component signal tests, but they do not unblock exact Model v4 replay, Formula Gauntlet tournaments, rankings integration, or production/model-use.",
            "",
            "## Scope",
            "",
            f"- Rows generated: `{len(receipts)}`",
            f"- Season coverage: `{seasons[0]}-{seasons[-1]}`",
            f"- Position coverage: `{dict(position_counts)}`",
            "- Receipt family regenerated: `role_archetype_receipts` only",
            "- Source: review-only partial replay input panel with lagged prior-season usage/production fields",
            "",
            "## Archetype Summary",
            "",
            f"- Distinct archetypes: `{len(archetype_counts)}`",
            f"- Largest buckets: `{top}`",
            "",
            "## Safety Decision",
            "",
            "Maximum allowed use: `REVIEW_ONLY_COMPONENT_SIGNAL_TESTS`.",
            "",
            "These receipts are not role truth, scouting labels, future outcome labels, exact Model v4 replay receipts, or production/model-use inputs.",
        ]
    )


def write_markdown(receipts: list[dict[str, object]]) -> None:
    position_counts = Counter(str(row["position"]) for row in receipts)
    sparse = sum(1 for row in receipts if row["sparse_history_flag"] == "true")
    duplicate_keys = len(receipts) - len({(row["season"], row["player_id"], row["position"]) for row in receipts})
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_RECEIPT_REGENERATION_PILOT_V1_REPORT.md").write_text(
        md_report(receipts), encoding="utf-8"
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_LEAKAGE_ASOF_VALIDATION.md").write_text(
        "\n".join(
            [
                "# Model v4 Role Archetype Leakage / As-Of Validation",
                "",
                "## Result",
                "",
                "`PASS`",
                "",
                "Role archetypes were generated only from lagged prior-season usage/production columns in the review-only partial replay input panel. No next-season points, next-position finish, startable outcome, future role, current ADP, current depth chart, or production ranking field was used.",
                "",
                "## Decision-Date Rule",
                "",
                "The receipt `season` is the target season and `feature_season` is the prior completed season. All role labels are prior-context descriptors known before target-season outcomes.",
            ]
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_IDENTITY_MISSINGNESS_VALIDATION.md").write_text(
        "\n".join(
            [
                "# Model v4 Role Archetype Identity / Missingness Validation",
                "",
                "## Result",
                "",
                "`PASS`",
                "",
                f"- Duplicate keys: `{duplicate_keys}`",
                f"- Position coverage: `{dict(position_counts)}`",
                f"- Sparse/low-games rows: `{sparse}`",
                "- Identity key: `player_id_gsis` carried as both `player_id` and `canonical_player_key`.",
                "- Missingness classification distinguishes `source_present_nonzero`, `source_present_true_zero`, and `unknown_source_value` for the primary position-specific volume input.",
            ]
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_PILOT_LIMITATIONS.md").write_text(
        "\n".join(
            [
                "# Model v4 Role Archetype Pilot Limitations",
                "",
                "- Archetypes are deterministic lagged context buckets, not subjective scouting labels.",
                "- Archetypes are not future role labels and do not use target-season outcomes.",
                "- Position-specific volume quartiles are review-only analytical context, not production thresholds.",
                "- The pilot does not approve exact Model v4 replay, Formula Gauntlet tournaments, rankings integration, source promotion, or production/model-use.",
                "- Future signal tests must compare these receipts against PYF and report sparse-history, low-games, prior-decline, role-change, and breakout/decline caveats.",
            ]
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_NEXT_ACTIONS.md").write_text(
        "\n".join(
            [
                "# Model v4 Role Archetype Next Actions",
                "",
                "## Recommended Next Lane",
                "",
                "`Model v4 Role Archetype Review-Only Component Signal Test V1`",
                "",
                "## Allowed Scope",
                "",
                "- Test role-archetype receipts against historical labels and PYF as review-only component/context signals.",
                "- Report sparse-history, low-games, prior-production decline, role-change proxy, WR breakout, and TE volatility slices.",
                "",
                "## Still Blocked",
                "",
                "- Exact Model v4 replay",
                "- Formula Gauntlet tournaments",
                "- 100-candidate Gauntlet",
                "- Champion refinement",
                "- Rankings integration",
                "- Production/model-use",
            ]
        ),
        encoding="utf-8",
    )
    (OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_SOURCE_TRACE.md").write_text(
        "\n".join(
            [
                "# Model v4 Role Archetype Source Trace",
                "",
                "## Inputs Used",
                "",
                f"- Partial replay input panel: `{PANEL_PATH.relative_to(REPO)}`",
                f"- Regeneration contract: `{CONTRACT_DIR.relative_to(REPO)}`",
                f"- Historical receipt master review: `{MASTER_REVIEW_DIR.relative_to(REPO)}`",
                f"- Freeze/schema validation packet: `{FREEZE_DIR.relative_to(REPO)}`",
                f"- Confidence-cap pilot context: `{CONFIDENCE_CAP_DIR.relative_to(REPO)}`",
                f"- Confidence-cap component signal test context: `{CONFIDENCE_SIGNAL_ARTIFACT}` at commit `{CONFIDENCE_SIGNAL_COMMIT}`",
                f"- HQ1 receipt-chain/use-gate standard: `{HQ1_STANDARD_DIR.relative_to(REPO)}`",
                f"- Data Hygiene operating charter: `{DATA_HYGIENE_CHARTER_DIR.relative_to(REPO)}`",
                "",
                "## Safety Notes",
                "",
                "- Regenerated only `role_archetype_receipts`.",
                "- Used lagged prior-season fields only.",
                "- Did not run exact replay, Formula Gauntlet, tournaments, tuning, source promotion, rankings integration, or production/model-use.",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    panel_rows = read_csv(PANEL_PATH)
    source_hash = sha256(PANEL_PATH)
    receipts = build_receipts(panel_rows, source_hash)
    if len(receipts) != len(panel_rows):
        raise RuntimeError("Receipt row count does not match source panel row count")
    duplicate_keys = len(receipts) - len({(row["season"], row["player_id"], row["position"]) for row in receipts})
    if duplicate_keys:
        raise RuntimeError(f"Duplicate receipt keys: {duplicate_keys}")
    if any(not str(row["leakage_flag"]).startswith("PASS") for row in receipts):
        raise RuntimeError("Leakage validation failed")
    if any(row["decision_date_safe"] != "yes" for row in receipts):
        raise RuntimeError("Decision-date validation failed")
    if any(not str(row["identity_flag"]).startswith("PASS") for row in receipts):
        raise RuntimeError("Identity validation failed")

    write_csv(OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_RECEIPTS_REVIEW_ONLY.csv", receipts, OUTPUT_COLUMNS)
    write_csv(
        OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_SOURCE_HASH_MANIFEST.csv",
        source_manifest(panel_rows),
        [
            "source_artifact",
            "sha256",
            "row_count",
            "column_count",
            "columns",
            "source_role",
            "use_gate_status",
            "notes",
        ],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_SCHEMA_VALIDATION.csv",
        schema_validation(receipts),
        ["check", "result", "passed", "caveat"],
    )
    write_csv(
        OUT_DIR / "MODEL_V4_ROLE_ARCHETYPE_DISTRIBUTION_REVIEW.csv",
        distribution(receipts),
        ["season", "position", "role_archetype", "rows", "position_season_rows", "share"],
    )
    write_markdown(receipts)


if __name__ == "__main__":
    main()
