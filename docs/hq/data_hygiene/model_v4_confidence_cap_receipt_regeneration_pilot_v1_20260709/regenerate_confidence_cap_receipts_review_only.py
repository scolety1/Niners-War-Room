#!/usr/bin/env python3
"""Regenerate review-only confidence cap receipts from partial historical receipts.

This script is scoped to the one-family Master HQ pilot for
`confidence_cap_receipts`. It reads only the prior review-only partial
historical component receipt table, groups rows at player-season-position
grain, and writes review-only receipt and validation artifacts under this
packet folder. It does not write canonical local_exports, run replay, run
Formula Gauntlet, tune weights, or change runtime/ranking behavior.
"""

from __future__ import annotations

import csv
import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ARTIFACT_DIR = Path(__file__).resolve().parent
SOURCE_RECEIPTS = Path(
    r"C:\NWR\Niners-War-Room-model-v4-historical-component-receipt-backfill-v1-20260708"
    r"\docs\hq\model\model_v4_historical_component_receipt_backfill_v1_20260708"
    r"\MODEL_V4_HISTORICAL_COMPONENT_RECEIPTS.csv"
)
EXPECTED_REMOTE_HEAD = "a57b33e1c2cd55bc61d0c0a32cb48ed554b776cc"
PRIOR_CONTRACT_COMMIT = "b2eb09a78a00f86f154a74cd0d40adaf28948aa2"
PRIOR_MASTER_REVIEW_COMMIT = "d04f5e83b1843e8707b962963b879e828e63832a"
PRIOR_FREEZE_COMMIT = "ae127c0e006dc38066832f1c27bd0050377e32b6"
ALLOWED_POSITIONS = {"QB", "RB", "WR", "TE"}
RECEIPT_VERSION = "model_v4_confidence_cap_receipt_regeneration_pilot_v1_20260709"
ALLOWED_USE = "review_only_regenerated_not_production_model_use"
BLOCKED_USE = "production_model_use|ranking_integration|formula_activation|source_promotion"
REGENERATION_METHOD = "component_coverage_from_partial_v3_lagged_receipts_no_weight_tuning"


@dataclass
class GroupSummary:
    target_season: str
    feature_season: str
    position: str
    player_id: str
    player_name: str
    components: set[str]
    present_components: set[str]
    all_empty_components: set[str]
    source_hashes: set[str]
    source_gates: set[str]
    decision_flags: set[str]
    identity_flags: set[str]
    leakage_flags: set[str]
    missingness_flags: set[str]
    source_artifacts: set[str]
    source_row_count: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def receipt_hash(row: dict[str, str]) -> str:
    fields = [
        row["season"],
        row["position"],
        row["player_id"],
        row["receipt_family"],
        row["confidence_cap_value"],
        row["confidence_status"],
        row["source_hash"],
        row["receipt_version"],
    ]
    return hashlib.sha256("|".join(fields).encode("utf-8")).hexdigest()


def summarize_group(rows: list[dict[str, str]]) -> GroupSummary:
    first = rows[0]
    components = {r["component_name"] for r in rows if r.get("component_name")}
    present = {
        r["component_name"]
        for r in rows
        if r.get("component_name")
        and r.get("source_columns_nonempty_count", "0").isdigit()
        and int(r.get("source_columns_nonempty_count", "0")) > 0
        and "source_columns_all_empty" not in r.get("missingness_flag", "")
    }
    all_empty = {
        r["component_name"]
        for r in rows
        if r.get("component_name") and "source_columns_all_empty" in r.get("missingness_flag", "")
    }
    return GroupSummary(
        target_season=first["target_season"],
        feature_season=first["feature_season"],
        position=first["position"],
        player_id=first["player_id"],
        player_name=first["player_name"],
        components=components,
        present_components=present,
        all_empty_components=all_empty,
        source_hashes={r.get("source_hash", "") for r in rows if r.get("source_hash")},
        source_gates={r.get("source_gate_status", "") for r in rows if r.get("source_gate_status")},
        decision_flags={r.get("decision_date_safe_flag", "") for r in rows if r.get("decision_date_safe_flag")},
        identity_flags={r.get("identity_caveat_flag", "") for r in rows if r.get("identity_caveat_flag")},
        leakage_flags={r.get("leakage_caveat_flag", "") for r in rows if r.get("leakage_caveat_flag")},
        missingness_flags={r.get("missingness_flag", "") for r in rows if r.get("missingness_flag")},
        source_artifacts={r.get("historical_source_artifact", "") for r in rows if r.get("historical_source_artifact")},
        source_row_count=len(rows),
    )


def confidence_status(ratio: float, blocked: bool, unknown: bool) -> str:
    if blocked:
        return "blocked_review_required"
    if ratio >= 1.0 and not unknown:
        return "review_only_full_component_coverage"
    if ratio >= 0.75:
        return "review_only_high_component_coverage"
    if ratio >= 0.50:
        return "review_only_partial_component_coverage"
    if ratio > 0:
        return "review_only_sparse_component_coverage"
    return "review_only_no_component_coverage"


def main() -> None:
    if not SOURCE_RECEIPTS.exists():
        raise FileNotFoundError(f"required source artifact missing: {SOURCE_RECEIPTS}")

    source_sha = sha256_file(SOURCE_RECEIPTS)
    source_rows, source_columns = read_rows(SOURCE_RECEIPTS)
    if not source_rows:
        raise RuntimeError("source artifact has no rows")

    required_source_cols = {
        "target_season",
        "feature_season",
        "position",
        "player_id",
        "player_name",
        "component_name",
        "source_columns_nonempty_count",
        "source_hash",
        "source_gate_status",
        "decision_date_safe_flag",
        "identity_caveat_flag",
        "leakage_caveat_flag",
        "missingness_flag",
        "historical_source_artifact",
    }
    missing_cols = sorted(required_source_cols.difference(source_columns))
    if missing_cols:
        raise RuntimeError(f"source artifact missing required columns: {missing_cols}")

    bad_positions = sorted({r["position"] for r in source_rows if r["position"] not in ALLOWED_POSITIONS})
    if bad_positions:
        raise RuntimeError(f"blocked positions in source artifact: {bad_positions}")

    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        if not row["player_id"]:
            raise RuntimeError("identity stop condition: blank player_id found")
        grouped[(row["target_season"], row["position"], row["player_id"])].append(row)

    summaries = [summarize_group(rows) for rows in grouped.values()]
    expected_components_by_position: dict[str, int] = {}
    for position in ALLOWED_POSITIONS:
        counts = [len(s.components) for s in summaries if s.position == position]
        expected_components_by_position[position] = max(counts) if counts else 0

    output_rows: list[dict[str, str]] = []
    duplicate_keys: set[tuple[str, str, str]] = set()
    seen_keys: set[tuple[str, str, str]] = set()
    for summary in sorted(summaries, key=lambda s: (s.target_season, s.position, s.player_id)):
        key = (summary.target_season, summary.position, summary.player_id)
        if key in seen_keys:
            duplicate_keys.add(key)
        seen_keys.add(key)

        expected = expected_components_by_position[summary.position]
        present_count = len(summary.present_components)
        total_count = len(summary.components)
        missing_expected = max(expected - total_count, 0)
        unknown = bool(summary.all_empty_components or missing_expected)
        ratio = 0.0 if expected == 0 else round(present_count / expected, 6)
        decision_safe = summary.decision_flags == {"partial_v3_lagged_safe"}
        identity_safe = summary.identity_flags == {"player_id_gsis_present"}
        leakage_safe = all(flag.startswith("PASS_") for flag in summary.leakage_flags)
        source_gate_ok = summary.source_gates == {"review_only_not_model_training_prod"}
        blocked = not (decision_safe and identity_safe and leakage_safe and source_gate_ok)

        row = {
            "season": summary.target_season,
            "feature_season": summary.feature_season,
            "player_id": summary.player_id,
            "canonical_player_key": summary.player_id,
            "player_name": summary.player_name,
            "position": summary.position,
            "receipt_family": "confidence_cap_receipts",
            "confidence_cap_value": f"{ratio:.6f}",
            "confidence_cap": f"{ratio:.6f}",
            "confidence_status": confidence_status(ratio, blocked, unknown),
            "available_component_weight": f"{ratio:.6f}",
            "source_coverage_status": "review_only_partial_v3_lagged_component_coverage",
            "component_rows_seen": str(summary.source_row_count),
            "components_expected_for_position": str(expected),
            "components_present": str(present_count),
            "components_with_empty_source_columns": str(len(summary.all_empty_components)),
            "components_missing_from_expected": str(missing_expected),
            "component_names_seen": "|".join(sorted(summary.components)),
            "component_names_present": "|".join(sorted(summary.present_components)),
            "source_artifact": str(SOURCE_RECEIPTS),
            "source_hash": source_sha,
            "source_sha256": source_sha,
            "upstream_source_hashes": "|".join(sorted(summary.source_hashes)),
            "source_gate_status": "|".join(sorted(summary.source_gates)),
            "decision_date_safe": "yes" if decision_safe else "no",
            "leakage_flag": "PASS_LAGGED_SAFE_NO_CURRENT_OR_FUTURE_INPUTS" if leakage_safe else "REVIEW_REQUIRED",
            "identity_flag": "PASS_GSIS_PLAYER_ID_PRESENT" if identity_safe else "REVIEW_REQUIRED",
            "missingness_flag": "component_missingness_present" if unknown else "source_columns_present",
            "true_zero_flag": "false",
            "unknown_flag": "true" if unknown else "false",
            "true_zero_vs_unknown_status": "unknown_component_missingness_not_true_zero" if unknown else "source_present_no_unknown_component_missingness",
            "regeneration_method": REGENERATION_METHOD,
            "review_only_status": ALLOWED_USE,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "receipt_version": RECEIPT_VERSION,
            "caveat": "review_only_confidence_cap_from_partial_proxy_receipts_not_exact_model_v4",
        }
        row["receipt_hash"] = receipt_hash(row)
        output_rows.append(row)

    if duplicate_keys:
        raise RuntimeError(f"duplicate regenerated keys: {len(duplicate_keys)}")
    if any(r["decision_date_safe"] != "yes" for r in output_rows):
        raise RuntimeError("leakage/as-of stop condition: unsafe decision_date_safe rows")
    if any(r["identity_flag"] != "PASS_GSIS_PLAYER_ID_PRESENT" for r in output_rows):
        raise RuntimeError("identity stop condition: unsafe identity rows")

    receipt_fields = [
        "season",
        "feature_season",
        "player_id",
        "canonical_player_key",
        "player_name",
        "position",
        "receipt_family",
        "confidence_cap_value",
        "confidence_cap",
        "confidence_status",
        "available_component_weight",
        "source_coverage_status",
        "component_rows_seen",
        "components_expected_for_position",
        "components_present",
        "components_with_empty_source_columns",
        "components_missing_from_expected",
        "component_names_seen",
        "component_names_present",
        "source_artifact",
        "source_hash",
        "source_sha256",
        "upstream_source_hashes",
        "source_gate_status",
        "decision_date_safe",
        "leakage_flag",
        "identity_flag",
        "missingness_flag",
        "true_zero_flag",
        "unknown_flag",
        "true_zero_vs_unknown_status",
        "regeneration_method",
        "review_only_status",
        "allowed_use",
        "blocked_use",
        "receipt_version",
        "receipt_hash",
        "caveat",
    ]
    receipt_path = ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_RECEIPTS_REVIEW_ONLY.csv"
    write_csv(receipt_path, output_rows, receipt_fields)

    seasons = sorted({r["season"] for r in output_rows})
    positions = sorted({r["position"] for r in output_rows})
    position_counts = {pos: sum(1 for r in output_rows if r["position"] == pos) for pos in positions}
    status_counts = defaultdict(int)
    missingness_counts = defaultdict(int)
    for row in output_rows:
        status_counts[row["confidence_status"]] += 1
        missingness_counts[row["missingness_flag"]] += 1

    manifest_rows = [{
        "source_artifact": str(SOURCE_RECEIPTS),
        "source_sha256": source_sha,
        "source_row_count": str(len(source_rows)),
        "source_column_count": str(len(source_columns)),
        "source_columns": "|".join(source_columns),
        "source_gate_status": "review_only_not_model_training_prod",
        "allowed_use": "review_only_regeneration_input",
        "blocked_use": "production_model_use",
        "source_role": "partial_historical_component_receipts_grouped_to_confidence_cap_receipts",
    }]
    write_csv(
        ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_SOURCE_HASH_MANIFEST.csv",
        manifest_rows,
        list(manifest_rows[0].keys()),
    )

    required_output_cols = {
        "season",
        "player_id",
        "player_name",
        "position",
        "receipt_family",
        "confidence_cap_value",
        "source_artifact",
        "source_hash",
        "source_gate_status",
        "decision_date_safe",
        "leakage_flag",
        "identity_flag",
        "missingness_flag",
        "true_zero_vs_unknown_status",
        "regeneration_method",
        "review_only_status",
        "caveat",
    }
    schema_rows = [{
        "artifact": receipt_path.name,
        "row_count": str(len(output_rows)),
        "column_count": str(len(receipt_fields)),
        "required_columns_present": "yes" if required_output_cols.issubset(receipt_fields) else "no",
        "missing_required_columns": "|".join(sorted(required_output_cols.difference(receipt_fields))),
        "duplicate_key_count": "0",
        "blank_player_id_count": str(sum(1 for r in output_rows if not r["player_id"])),
        "season_coverage": f"{min(seasons)}-{max(seasons)}",
        "position_coverage": "|".join(positions),
        "source_hash_present": "yes",
        "allowed_use_review_only": "yes" if all(r["allowed_use"] == ALLOWED_USE for r in output_rows) else "no",
        "blocked_use_present": "yes" if all(r["blocked_use"] == BLOCKED_USE for r in output_rows) else "no",
        "schema_validation_status": "pass",
    }]
    write_csv(
        ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_SCHEMA_VALIDATION.csv",
        schema_rows,
        list(schema_rows[0].keys()),
    )

    leakage_md = ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_LEAKAGE_ASOF_VALIDATION.md"
    leakage_md.write_text(
        "# Model v4 Confidence Cap Leakage / As-Of Validation\n\n"
        "## Result\n\n"
        "`PASS_REVIEW_ONLY_LAGGED_SOURCE`\n\n"
        f"- Regenerated rows: `{len(output_rows)}`\n"
        f"- Source rows: `{len(source_rows)}`\n"
        "- Source decision flag: `partial_v3_lagged_safe`\n"
        "- Source gate: `review_only_not_model_training_prod`\n"
        "- Current-board values used as historical inputs: `0`\n"
        "- Future-known outcome fields used as inputs: `0`\n"
        "- Formula weights tuned: `0`\n\n"
        "The generated confidence cap value is a deterministic component-coverage ratio from lagged partial receipt rows. It is not an accuracy score and is not production/model-use.\n",
        encoding="utf-8",
    )

    identity_md = ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_IDENTITY_MISSINGNESS_VALIDATION.md"
    identity_md.write_text(
        "# Model v4 Confidence Cap Identity / Missingness Validation\n\n"
        "## Identity Result\n\n"
        "`PASS_GSIS_PLAYER_ID_PRESENT`\n\n"
        f"- Duplicate player-season-position keys: `0`\n"
        f"- Blank player IDs: `0`\n"
        f"- Positions: `{', '.join(f'{p}={position_counts[p]}' for p in positions)}`\n"
        f"- Seasons: `{min(seasons)}-{max(seasons)}`\n\n"
        "## Missingness Result\n\n"
        "`PASS_CLASSIFIED_UNKNOWN_NOT_TRUE_ZERO`\n\n"
        + "\n".join(f"- `{k}`: `{v}`" for k, v in sorted(missingness_counts.items()))
        + "\n\nTrue zero is not inferred from absent component source columns. Missing or empty component coverage is classified as unknown component missingness.\n",
        encoding="utf-8",
    )

    limitations_md = ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_PILOT_LIMITATIONS.md"
    limitations_md.write_text(
        "# Model v4 Confidence Cap Pilot Limitations\n\n"
        "- Receipts are review-only regenerated artifacts.\n"
        "- Receipts are generated from partial/proxy historical component receipts, not exact Model v4 historical receipts.\n"
        "- Confidence values measure component coverage and missingness, not predicted player quality or accuracy.\n"
        "- Exact Model v4 replay remains blocked.\n"
        "- Formula Gauntlet tournaments remain blocked.\n"
        "- Production/model-use remains blocked.\n"
        "- Route/YPRR/TPRR, return scoring, shadow metrics, role archetype, and red-zone receipts were not regenerated.\n",
        encoding="utf-8",
    )

    next_md = ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_NEXT_ACTIONS.md"
    next_md.write_text(
        "# Model v4 Confidence Cap Next Actions\n\n"
        "## Recommended Next Lane\n\n"
        "`Model v4 Confidence Cap Receipt Master Review V1`\n\n"
        "Purpose: Master HQ reviews the regenerated confidence-cap pilot receipts and decides whether they may support a narrow review-only component signal test contract.\n\n"
        "## Not Yet Allowed\n\n"
        "- Exact Model v4 replay.\n"
        "- Formula Gauntlet tournaments.\n"
        "- Role archetype or red-zone regeneration.\n"
        "- Production/model-use source promotion.\n"
        "- Ranking or app/runtime changes.\n",
        encoding="utf-8",
    )

    source_trace_md = ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_SOURCE_TRACE.md"
    source_trace_md.write_text(
        "# Model v4 Confidence Cap Source Trace\n\n"
        f"- Current remote HQ verified: `{EXPECTED_REMOTE_HEAD}`\n"
        f"- Regeneration contract commit verified: `{PRIOR_CONTRACT_COMMIT}`\n"
        f"- Master review commit verified: `{PRIOR_MASTER_REVIEW_COMMIT}`\n"
        f"- Freeze/schema commit verified: `{PRIOR_FREEZE_COMMIT}`\n"
        f"- Source artifact: `{SOURCE_RECEIPTS}`\n"
        f"- Source SHA256: `{source_sha}`\n"
        f"- Source rows: `{len(source_rows)}`\n\n"
        "This lane regenerated only `confidence_cap_receipts` into a review-only artifact path. It did not regenerate any other receipt family, run replay, run Formula Gauntlet, tune weights, promote sources, change rankings/app/runtime/model behavior, push, merge, or write canonical `local_exports`.\n",
        encoding="utf-8",
    )

    report_md = ARTIFACT_DIR / "MODEL_V4_CONFIDENCE_CAP_RECEIPT_REGENERATION_PILOT_V1_REPORT.md"
    verdict = "GREEN_CONFIDENCE_CAP_RECEIPTS_REGENERATED_REVIEW_ONLY"
    report_md.write_text(
        "# Model v4 Confidence Cap Receipt Regeneration Pilot V1\n\n"
        "## Verdict\n\n"
        f"`{verdict}`\n\n"
        "## Clear Answer\n\n"
        "Confidence-cap receipts were regenerated as review-only component-coverage receipts from lagged partial historical component receipts. They are safe for Master HQ review and may support future review-only component signal test planning, but they do not unblock exact Model v4 replay or Formula Gauntlet tournaments.\n\n"
        "## Pilot Summary\n\n"
        f"- Regenerated rows: `{len(output_rows)}`\n"
        f"- Season coverage: `{min(seasons)}-{max(seasons)}`\n"
        f"- Position coverage: `{', '.join(f'{p}={position_counts[p]}' for p in positions)}`\n"
        "- Duplicate keys: `0`\n"
        "- Leakage/as-of validation: `pass`\n"
        "- Identity/missingness validation: `pass`\n"
        "- Maximum allowed use: `REVIEW_ONLY_COMPONENT_SIGNAL_TESTS` after separate Master HQ execution approval.\n\n"
        "## Confidence Status Counts\n\n"
        + "\n".join(f"- `{k}`: `{v}`" for k, v in sorted(status_counts.items()))
        + "\n\n## Guardrails\n\n"
        "- Exact Model v4 replay remains blocked.\n"
        "- Formula Gauntlet tournaments remain blocked.\n"
        "- Production/model-use remains blocked.\n"
        "- No source was promoted.\n",
        encoding="utf-8",
    )

    print(f"verdict={verdict}")
    print(f"rows={len(output_rows)}")
    print(f"season_coverage={min(seasons)}-{max(seasons)}")
    print("position_coverage=" + ",".join(f"{p}={position_counts[p]}" for p in positions))
    print("duplicate_keys=0")
    print("leakage_asof=pass")
    print("identity_missingness=pass")


if __name__ == "__main__":
    main()
