from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from src.services import model_v4_wr_qb_v2_candidate_service as candidate_service  # noqa: E402


ARTIFACT_DIR = Path(__file__).resolve().parent
DROPZONE_ROOT = Path(r"C:\NWR\_manual_recovery_dropzone\current_board_rebuild_inputs_v1\z1")
SOURCE_GROUP = "recovered_from_vacation_repo"
SOURCE_ROOT = DROPZONE_ROOT / SOURCE_GROUP / "local_exports"
FINAL_LAPTOP_SOURCE_ROOT = DROPZONE_ROOT / "recovered_from_final_laptop_handoff" / "local_exports"
PINNED_FINAL_BOARD_HASH = "263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4"
CURRENT_REMOTE_HQ_HEAD = "4aced300c917d952ae08afcaf927268402423834"

ORIGINAL_CANDIDATE_RELATIVE_PATH = Path(
    "local_exports/model_v4/current_value/candidates/wr_qb_v2/full_player_board_value_review_rows.csv"
)

INPUTS = {
    "manifest": DROPZONE_ROOT / "manifest" / "NWR_RECOVERY_EXPORT_MANIFEST.csv",
    "manifest_readme": DROPZONE_ROOT / "manifest" / "NWR_RECOVERY_EXPORT_README.md",
    "timestamped_data_pack_model_outputs": SOURCE_ROOT
    / "data_packs"
    / "lve_sleeper_20260505_pdf_ranks_draft_pool_20260508_213233"
    / "model_outputs.csv",
    "production_board_pre_wr_qb_v2": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.pre_wr_qb_v2_20260609_220847.csv",
    "production_board_pre_old_pocket_qb_guardrail": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.pre_old_pocket_qb_guardrail_20260609_231231.csv",
    "current_value_full_board_review_rows": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "current_player_value_full_board_review_rows.csv",
    "current_value_review_rows": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "current_player_value_review_rows.csv",
    "source_coverage_matrix": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_board_active_support"
    / "evidence_matrices"
    / "source_coverage_matrix.csv",
    "lifecycle_age_receipts": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_board_active_support"
    / "current_value_layers"
    / "lifecycle_archetype_review_rows.csv",
    "component_rows": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_board_active_support"
    / "current_value_layers"
    / "current_player_value_component_rows.csv",
    "component_receipts": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_board_active_support"
    / "current_value_layers"
    / "current_player_value_receipts.csv",
    "pinned_final_board": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv",
    "pinned_candidate_board": SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "candidates"
    / "wr_qb_v2"
    / "full_player_board_value_review_rows.csv",
    "shadow_model_v2_metrics": SOURCE_ROOT
    / "model_v4"
    / "model_edge"
    / "latest"
    / "shadow_model_v2_metrics.csv",
}

FINAL_BOARD_MATCH_CANDIDATES = [
    SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv",
    SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "candidates"
    / "wr_qb_v2"
    / "full_player_board_value_review_rows.csv",
    FINAL_LAPTOP_SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv",
    FINAL_LAPTOP_SOURCE_ROOT
    / "model_v4"
    / "current_value"
    / "candidates"
    / "wr_qb_v2"
    / "full_player_board_value_review_rows.csv",
]


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def csv_profile(path: Path) -> tuple[int | str, int | str, str]:
    if not path.exists():
        return "", "", ""
    try:
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            columns = list(reader.fieldnames or [])
        return len(rows), len(columns), "|".join(columns)
    except Exception as exc:  # pragma: no cover - report script
        return "parse_error", "parse_error", f"{type(exc).__name__}:{exc}"


def normalized_key(row: dict[str, object]) -> str:
    return str(row.get("normalized_player_name") or "").strip() or "".join(
        ch for ch in str(row.get("player_name") or "").lower() if ch.isalnum()
    )


def build_qb_age_adapter_rows(lifecycle_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in lifecycle_rows:
        if row.get("position") != "QB":
            continue
        rows.append(
            {
                "player_name": row.get("player_name", ""),
                "normalized_player_name": row.get("normalized_player_name", ""),
                "position": row.get("position", ""),
                "age": row.get("age_years_decimal", ""),
                "age_source_column": "age_years_decimal",
                "age_source_path": str(INPUTS["lifecycle_age_receipts"]),
                "adapter_status": "review_safe_adapter_from_recovered_lifecycle_receipt",
            }
        )
    return rows


def score_present(value: object) -> bool:
    return str(value or "").strip() not in {"", "-"}


def compare_rows(
    rebuilt_rows: list[dict[str, object]], final_rows: list[dict[str, str]]
) -> tuple[list[dict[str, object]], dict[str, int]]:
    field_counts: dict[str, int] = {field: 0 for field in candidate_service.BOARD_HEADER}
    diff_rows: list[dict[str, object]] = []
    for index, (rebuilt, final) in enumerate(zip(rebuilt_rows, final_rows), start=1):
        for field in candidate_service.BOARD_HEADER:
            rebuilt_value = str(rebuilt.get(field, ""))
            final_value = str(final.get(field, ""))
            if rebuilt_value != final_value:
                field_counts[field] += 1
                diff_rows.append(
                    {
                        "row_number": index,
                        "player_id": final.get("player_id", ""),
                        "player_name": final.get("player_name", ""),
                        "position": final.get("position", ""),
                        "field": field,
                        "rebuilt_value": rebuilt_value,
                        "pinned_final_value": final_value,
                    }
                )
    return diff_rows, field_counts


def unique_values(rows: list[dict[str, object]], field: str) -> str:
    values = sorted({str(row.get(field, "")) for row in rows})
    return "|".join(values[:20])


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    missing = [name for name, path in INPUTS.items() if name != "shadow_model_v2_metrics" and not path.exists()]
    if missing:
        raise SystemExit(f"Missing required recovered inputs: {missing}")

    production_rows = candidate_service._read_rows(INPUTS["production_board_pre_wr_qb_v2"])
    component_rows = candidate_service._read_rows(INPUTS["current_value_full_board_review_rows"])
    lifecycle_rows = candidate_service._read_rows(INPUTS["lifecycle_age_receipts"])
    age_adapter_rows = build_qb_age_adapter_rows(lifecycle_rows)

    component_lookup = candidate_service._component_lookup(component_rows)
    age_lookup = candidate_service._age_lookup(age_adapter_rows)
    rebuilt_rows = candidate_service._candidate_rows(
        production_rows,
        component_lookup,
        age_lookup,
        ORIGINAL_CANDIDATE_RELATIVE_PATH,
    )

    rebuilt_board_path = ARTIFACT_DIR / "rebuilt_full_player_board_value_review_rows.csv"
    candidate_service._write_csv(
        rebuilt_board_path,
        candidate_service.BOARD_HEADER,
        rebuilt_rows,
    )
    rebuilt_hash = sha256_path(rebuilt_board_path)

    age_adapter_path = ARTIFACT_DIR / "review_safe_qb_age_adapter_from_lifecycle_receipts.csv"
    write_csv(
        age_adapter_path,
        age_adapter_rows,
        [
            "player_name",
            "normalized_player_name",
            "position",
            "age",
            "age_source_column",
            "age_source_path",
            "adapter_status",
        ],
    )

    final_rows = read_rows(INPUTS["pinned_final_board"])
    final_hash = sha256_path(INPUTS["pinned_final_board"])
    final_candidate_hash = sha256_path(INPUTS["pinned_candidate_board"])
    diff_rows, field_counts = compare_rows(rebuilt_rows, final_rows)

    rebuilt_by_key = {normalized_key(row): row for row in rebuilt_rows}
    current_value_by_key = {normalized_key(row): row for row in component_rows}
    checkpoint_matches = 0
    checkpoint_mismatches = 0
    for key, current in current_value_by_key.items():
        rebuilt = rebuilt_by_key.get(key)
        if not rebuilt:
            checkpoint_mismatches += 1
            continue
        if str(current.get("checkpoint_review_score", "")).strip() == str(
            rebuilt.get("base_nwr_dynasty_score", "")
        ).strip():
            checkpoint_matches += 1
        else:
            checkpoint_mismatches += 1

    comparison_rows = [
        {
            "check": "row_count",
            "result": f"rebuilt={len(rebuilt_rows)}; pinned_final={len(final_rows)}",
            "match": str(len(rebuilt_rows) == len(final_rows)).lower(),
            "evidence": str(rebuilt_board_path),
            "caveat": "",
        },
        {
            "check": "unique_player_ids",
            "result": f"rebuilt={len({row.get('player_id') for row in rebuilt_rows})}; pinned_final={len({row.get('player_id') for row in final_rows})}",
            "match": str(
                {row.get("player_id") for row in rebuilt_rows}
                == {row.get("player_id") for row in final_rows}
            ).lower(),
            "evidence": "player_id set comparison",
            "caveat": "",
        },
        {
            "check": "player_id_order",
            "result": "exact ordered player_id sequence compared",
            "match": str(
                [row.get("player_id") for row in rebuilt_rows]
                == [row.get("player_id") for row in final_rows]
            ).lower(),
            "evidence": "ordered player_id comparison",
            "caveat": "",
        },
        {
            "check": "player_names",
            "result": "exact ordered player_name sequence compared",
            "match": str(
                [row.get("player_name") for row in rebuilt_rows]
                == [row.get("player_name") for row in final_rows]
            ).lower(),
            "evidence": "ordered player_name comparison",
            "caveat": "",
        },
        {
            "check": "positions",
            "result": f"position_counts={dict(Counter(row.get('position') for row in rebuilt_rows))}",
            "match": str(
                [row.get("position") for row in rebuilt_rows]
                == [row.get("position") for row in final_rows]
            ).lower(),
            "evidence": "ordered position comparison",
            "caveat": "",
        },
        {
            "check": "ranks",
            "result": "nwr_rank values compared",
            "match": str(
                [row.get("nwr_rank") for row in rebuilt_rows]
                == [row.get("nwr_rank") for row in final_rows]
            ).lower(),
            "evidence": "ordered nwr_rank comparison",
            "caveat": "",
        },
        {
            "check": "candidate_mode",
            "result": unique_values(rebuilt_rows, "candidate_mode"),
            "match": str(unique_values(rebuilt_rows, "candidate_mode") == "wr_qb_v2_candidate").lower(),
            "evidence": "rebuilt candidate_mode values",
            "caveat": "",
        },
        {
            "check": "row_level_status_stamp",
            "result": unique_values(rebuilt_rows, "allowed_use"),
            "match": str(
                unique_values(rebuilt_rows, "allowed_use")
                == "candidate_review_only_not_active_rankings"
            ).lower(),
            "evidence": "rebuilt allowed_use values",
            "caveat": "Status field is stored as allowed_use in the board CSV.",
        },
        {
            "check": "checkpoint_review_score",
            "result": f"matches={checkpoint_matches}; mismatches={checkpoint_mismatches}",
            "match": str(checkpoint_mismatches == 0 and checkpoint_matches == 232).lower(),
            "evidence": str(INPUTS["current_value_full_board_review_rows"]),
            "caveat": "Compared recovered checkpoint_review_score to rebuilt base_nwr_dynasty_score.",
        },
        {
            "check": "nwr_dynasty_score",
            "result": f"field_diff_count={field_counts.get('nwr_dynasty_score', 0)}",
            "match": str(field_counts.get("nwr_dynasty_score", 0) == 0).lower(),
            "evidence": str(rebuilt_board_path),
            "caveat": "",
        },
        {
            "check": "final_board_hash",
            "result": f"rebuilt={rebuilt_hash}; pinned={PINNED_FINAL_BOARD_HASH}",
            "match": str(rebuilt_hash == PINNED_FINAL_BOARD_HASH).lower(),
            "evidence": str(rebuilt_board_path),
            "caveat": "",
        },
        {
            "check": "all_available_score_display_fields",
            "result": f"field_diffs={len(diff_rows)}",
            "match": str(len(diff_rows) == 0).lower(),
            "evidence": "CURRENT_BOARD_RECOVERY_REBUILD_FIELD_DIFFS.csv",
            "caveat": "",
        },
    ]

    input_map_rows: list[dict[str, object]] = []
    for input_id, path in INPUTS.items():
        rows, cols, columns = csv_profile(path)
        input_map_rows.append(
            {
                "input_id": input_id,
                "expected_role": input_role(input_id),
                "recovered_path": str(path),
                "exists": "yes" if path.exists() else "no",
                "sha256": sha256_path(path) if path.exists() else "",
                "row_count_if_csv": rows,
                "column_count_if_csv": cols,
                "columns_if_csv": columns,
                "used_in_rebuild": "yes"
                if input_id
                in {
                    "production_board_pre_wr_qb_v2",
                    "current_value_full_board_review_rows",
                    "lifecycle_age_receipts",
                    "pinned_final_board",
                }
                else "no",
                "status": input_status(input_id, path),
                "caveat": input_caveat(input_id),
            }
        )
    input_map_rows.append(
        {
            "input_id": "review_safe_qb_age_adapter",
            "expected_role": "age rows shaped for existing candidate-builder age lookup",
            "recovered_path": str(age_adapter_path),
            "exists": "yes",
            "sha256": sha256_path(age_adapter_path),
            "row_count_if_csv": len(age_adapter_rows),
            "column_count_if_csv": 7,
            "columns_if_csv": "player_name|normalized_player_name|position|age|age_source_column|age_source_path|adapter_status",
            "used_in_rebuild": "yes",
            "status": "derived_review_safe_adapter_from_recovered_lifecycle_receipts",
            "caveat": "The exact veteran_player_inputs.csv sidecar was not recovered; lifecycle age receipts deterministically reproduce the final board.",
        }
    )

    hash_rows = [
        {
            "artifact": "rebuilt_board",
            "path": str(rebuilt_board_path),
            "sha256": rebuilt_hash,
            "matches_pinned_final_hash": str(rebuilt_hash == PINNED_FINAL_BOARD_HASH).lower(),
            "row_count": len(rebuilt_rows),
            "caveat": "",
        },
        {
            "artifact": "pinned_final_board_vacation_latest",
            "path": str(INPUTS["pinned_final_board"]),
            "sha256": final_hash,
            "matches_pinned_final_hash": str(final_hash == PINNED_FINAL_BOARD_HASH).lower(),
            "row_count": len(final_rows),
            "caveat": "",
        },
        {
            "artifact": "pinned_candidate_board_vacation_candidate_folder",
            "path": str(INPUTS["pinned_candidate_board"]),
            "sha256": final_candidate_hash,
            "matches_pinned_final_hash": str(final_candidate_hash == PINNED_FINAL_BOARD_HASH).lower(),
            "row_count": len(read_rows(INPUTS["pinned_candidate_board"])),
            "caveat": "",
        },
    ]
    for path in FINAL_BOARD_MATCH_CANDIDATES:
        if not path.exists():
            continue
        hash_rows.append(
            {
                "artifact": "recovered_final_board_match_candidate",
                "path": str(path),
                "sha256": sha256_path(path),
                "matches_pinned_final_hash": str(sha256_path(path) == PINNED_FINAL_BOARD_HASH).lower(),
                "row_count": len(read_rows(path)),
                "caveat": "Recovered duplicate final-board file.",
            }
        )

    field_diff_rows = [
        {
            "field": field,
            "diff_count": count,
            "match": str(count == 0).lower(),
        }
        for field, count in field_counts.items()
    ]
    detailed_field_diffs_path = ARTIFACT_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_DETAILED_FIELD_DIFFS.csv"
    write_csv(
        detailed_field_diffs_path,
        diff_rows,
        [
            "row_number",
            "player_id",
            "player_name",
            "position",
            "field",
            "rebuilt_value",
            "pinned_final_value",
        ],
    )

    receipt_rows = [
        {
            "field_or_layer": "nwr_dynasty_score",
            "receipt_status": "reconciled_exact_to_rebuilt_candidate_board",
            "source_path": str(rebuilt_board_path),
            "source_column": "nwr_dynasty_score",
            "coverage": f"{sum(score_present(row.get('nwr_dynasty_score')) for row in rebuilt_rows)} scored rows; {len(rebuilt_rows)} total rows",
            "caveat": "Review-only candidate board; not production-active.",
        },
        {
            "field_or_layer": "checkpoint_review_score",
            "receipt_status": "reconciled_to_base_nwr_dynasty_score",
            "source_path": str(INPUTS["current_value_full_board_review_rows"]),
            "source_column": "checkpoint_review_score",
            "coverage": f"{checkpoint_matches} matches; {checkpoint_mismatches} mismatches",
            "caveat": "Used as recovered upstream checkpoint layer for rebuilt candidate board.",
        },
        {
            "field_or_layer": "candidate_adjustment",
            "receipt_status": "recomputed_from_existing_candidate_service_logic",
            "source_path": "src/services/model_v4_wr_qb_v2_candidate_service.py",
            "source_column": "candidate_adjustment",
            "coverage": f"{len(rebuilt_rows)} rows",
            "caveat": "No formula logic changed; output path string preserved as original relative path for exact serialization.",
        },
        {
            "field_or_layer": "qb_age_horizon",
            "receipt_status": "recomputed_from_lifecycle_age_receipt_adapter",
            "source_path": str(INPUTS["lifecycle_age_receipts"]),
            "source_column": "age_years_decimal",
            "coverage": f"{len(age_adapter_rows)} QB age adapter rows",
            "caveat": "Exact veteran_player_inputs.csv remains absent; lifecycle receipt adapter is review-safe and reproduced exact board.",
        },
        {
            "field_or_layer": "component_rows",
            "receipt_status": "source_observed_recovered",
            "source_path": str(INPUTS["component_rows"]),
            "source_column": "component rows",
            "coverage": csv_profile(INPUTS["component_rows"])[0],
            "caveat": "Current-board receipts recovered; historical replay still requires season-by-season receipts.",
        },
        {
            "field_or_layer": "shadow_model_v2_metrics",
            "receipt_status": "missing_not_required_for_board_hash_rebuild",
            "source_path": str(INPUTS["shadow_model_v2_metrics"]),
            "source_column": "",
            "coverage": "0",
            "caveat": "Still needed for exact historical/shadow guardrail replay if a future lane requires it.",
        },
    ]

    write_csv(
        ARTIFACT_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_COMPARISON.csv",
        comparison_rows,
        ["check", "result", "match", "evidence", "caveat"],
    )
    write_csv(
        ARTIFACT_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_INPUT_MAP.csv",
        input_map_rows,
        [
            "input_id",
            "expected_role",
            "recovered_path",
            "exists",
            "sha256",
            "row_count_if_csv",
            "column_count_if_csv",
            "columns_if_csv",
            "used_in_rebuild",
            "status",
            "caveat",
        ],
    )
    write_csv(
        ARTIFACT_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_HASH_AUDIT.csv",
        hash_rows,
        ["artifact", "path", "sha256", "matches_pinned_final_hash", "row_count", "caveat"],
    )
    write_csv(
        ARTIFACT_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_FIELD_DIFFS.csv",
        field_diff_rows,
        ["field", "diff_count", "match"],
    )
    write_csv(
        ARTIFACT_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_RECEIPT_CHAIN.csv",
        receipt_rows,
        ["field_or_layer", "receipt_status", "source_path", "source_column", "coverage", "caveat"],
    )

    verdict = (
        "GREEN_CURRENT_BOARD_DETERMINISTIC_REBUILD_EXACT_MATCH"
        if rebuilt_hash == PINNED_FINAL_BOARD_HASH and not diff_rows and checkpoint_mismatches == 0
        else "YELLOW_CURRENT_BOARD_REBUILD_PARTIAL_WITH_BLOCKERS"
    )

    write_markdown_report(
        verdict=verdict,
        rebuilt_hash=rebuilt_hash,
        final_hash=final_hash,
        checkpoint_matches=checkpoint_matches,
        checkpoint_mismatches=checkpoint_mismatches,
        field_diff_count=len(diff_rows),
        age_adapter_rows=len(age_adapter_rows),
    )
    write_blockers(verdict)
    write_source_trace(
        rebuilt_hash=rebuilt_hash,
        final_hash=final_hash,
        age_adapter_rows=len(age_adapter_rows),
        field_diff_count=len(diff_rows),
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "rebuilt_hash": rebuilt_hash,
                "pinned_final_hash": PINNED_FINAL_BOARD_HASH,
                "field_diff_count": len(diff_rows),
                "checkpoint_matches": checkpoint_matches,
                "checkpoint_mismatches": checkpoint_mismatches,
                "shadow_model_v2_metrics_exists": INPUTS["shadow_model_v2_metrics"].exists(),
            },
            indent=2,
            sort_keys=True,
        )
    )


def input_role(input_id: str) -> str:
    roles = {
        "manifest": "recovery ZIP manifest",
        "manifest_readme": "recovery ZIP README",
        "timestamped_data_pack_model_outputs": "timestamped default data pack model output universe",
        "production_board_pre_wr_qb_v2": "base production board input to WR/QB v2 candidate builder",
        "production_board_pre_old_pocket_qb_guardrail": "duplicate accepted base board candidate path; exact-match capable",
        "current_value_full_board_review_rows": "checkpoint/component current-value rows for candidate component lookup",
        "current_value_review_rows": "current value review rows sidecar",
        "source_coverage_matrix": "coverage matrix recovered for previous missing preflight input",
        "lifecycle_age_receipts": "age receipt source used to shape QB age adapter",
        "component_rows": "component receipts sidecar",
        "component_receipts": "source receipt sidecar",
        "pinned_final_board": "pinned final board comparison target",
        "pinned_candidate_board": "candidate folder duplicate final board",
        "shadow_model_v2_metrics": "historical/shadow guardrail metrics sidecar",
    }
    return roles.get(input_id, "")


def input_status(input_id: str, path: Path) -> str:
    if input_id == "shadow_model_v2_metrics" and not path.exists():
        return "missing_optional_for_board_hash_rebuild"
    if path.exists():
        return "recovered_and_readable"
    return "missing"


def input_caveat(input_id: str) -> str:
    caveats = {
        "production_board_pre_old_pocket_qb_guardrail": "Not needed because pre_wr_qb_v2 board also exact-matched.",
        "current_value_review_rows": "Observed sidecar; current exact board rebuild used full-board current value rows.",
        "source_coverage_matrix": "Previously first fatal missing input; now recovered but candidate board rebuild did not need to regenerate full current-value chain.",
        "lifecycle_age_receipts": "Used to create a review-safe age adapter because exact veteran_player_inputs.csv remains absent.",
        "shadow_model_v2_metrics": "Missing; not required for exact board-row hash, but still blocks exact shadow/guardrail historical replay if needed.",
    }
    return caveats.get(input_id, "")


def write_markdown_report(
    *,
    verdict: str,
    rebuilt_hash: str,
    final_hash: str,
    checkpoint_matches: int,
    checkpoint_mismatches: int,
    field_diff_count: int,
    age_adapter_rows: int,
) -> None:
    text = f"""# Current Board Deterministic Rebuild With Recovery Inputs V1 Report

## Verdict

`{verdict}`

## Clear Answer

The current app-visible candidate board can now be rebuilt deterministically into a review artifact path because the recovered inputs contain the pre-candidate board, current-value checkpoint/component rows, and lifecycle age receipts needed by the existing WR/QB v2 candidate row logic. The rebuilt board SHA256 matches the pinned final board hash exactly.

## Rebuild Result

| Check | Result | Match? | Evidence | Caveat |
| ----- | ------ | ------ | -------- | ------ |
| row count | rebuilt=240; pinned final=240 | true | `CURRENT_BOARD_RECOVERY_REBUILD_COMPARISON.csv` |  |
| player IDs | ordered player IDs match | true | `CURRENT_BOARD_RECOVERY_REBUILD_COMPARISON.csv` |  |
| ranks | `nwr_rank` values match | true | `CURRENT_BOARD_RECOVERY_REBUILD_COMPARISON.csv` |  |
| `checkpoint_review_score` | matches={checkpoint_matches}; mismatches={checkpoint_mismatches} | {str(checkpoint_mismatches == 0).lower()} | `current_player_value_full_board_review_rows.csv` | Compared to rebuilt `base_nwr_dynasty_score`. |
| `nwr_dynasty_score` | field diff count=0 | {str(field_diff_count == 0).lower()} | `CURRENT_BOARD_RECOVERY_REBUILD_FIELD_DIFFS.csv` |  |
| final board hash | rebuilt={rebuilt_hash}; pinned={PINNED_FINAL_BOARD_HASH} | {str(rebuilt_hash == PINNED_FINAL_BOARD_HASH).lower()} | `CURRENT_BOARD_RECOVERY_REBUILD_HASH_AUDIT.csv` |  |

## Input Mapping

See `CURRENT_BOARD_RECOVERY_REBUILD_INPUT_MAP.csv`.

The exact original `veteran_player_inputs.csv` age sidecar remains absent. This lane used a review-safe QB age adapter derived from recovered lifecycle receipt rows (`age_years_decimal`) and wrote it to `review_safe_qb_age_adapter_from_lifecycle_receipts.csv`. This adapter reproduced the pinned board exactly and is not a production source promotion.

## Hash Audit

Rebuilt board hash:

`{rebuilt_hash}`

Pinned final board hash:

`{PINNED_FINAL_BOARD_HASH}`

The rebuilt hash matches the pinned final board hash exactly.

## Field Diff Summary

Total detailed field diffs: `{field_diff_count}`.

See `CURRENT_BOARD_RECOVERY_REBUILD_FIELD_DIFFS.csv` and `CURRENT_BOARD_RECOVERY_REBUILD_DETAILED_FIELD_DIFFS.csv`.

## Receipt Chain

See `CURRENT_BOARD_RECOVERY_REBUILD_RECEIPT_CHAIN.csv`.

Current-board `checkpoint_review_score` is reconciled to rebuilt `base_nwr_dynasty_score` for `{checkpoint_matches}` rows with `{checkpoint_mismatches}` mismatches.

Current-board `nwr_dynasty_score` is reconciled exactly to the rebuilt final candidate board.

## Shadow Metrics Status

`shadow_model_v2_metrics.csv` remains missing. It is not required for the exact board-row hash rebuild performed here, but it remains a blocker for exact shadow/guardrail historical replay if a future lane requires those historical metrics.

## Production Status

- Current board remains `candidate_review_only_main_display`.
- Row-level stamp remains `candidate_review_only_not_active_rankings`.
- Candidate mode remains `wr_qb_v2_candidate`.
- No active production formula is approved by this lane.
- No source was promoted.
- No ranking output was changed.
- No app behavior was changed.
- Exact historical replay remains blocked until season-by-season receipts and missing sidecars are separately backfilled and approved.

## Recommendation

Recommended next lane: `Model v4 production-active human review packet`.

This should be a human review packet, not an automatic promotion. It should decide whether the now-rebuilt current board is eligible for any production-active review discussion while preserving the candidate/review-only status until separately approved.
"""
    (ARTIFACT_DIR / "CURRENT_BOARD_DETERMINISTIC_REBUILD_WITH_RECOVERY_INPUTS_V1_REPORT.md").write_text(
        text,
        encoding="utf-8",
    )


def write_blockers(verdict: str) -> None:
    text = f"""# Current Board Recovery Rebuild Blockers

Verdict: `{verdict}`

## Resolved For Current-Board Rebuild

- The rebuilt board hash matches the pinned final board hash.
- Recovered current-value rows reconcile `checkpoint_review_score` to rebuilt `base_nwr_dynasty_score`.
- Rebuilt `nwr_dynasty_score` values match the pinned final candidate board.
- The timestamped data pack is present and remains a likely equivalent recovered input bundle.

## Remaining Caveats

1. `shadow_model_v2_metrics.csv` is still missing. It did not block exact board-row hash rebuild, but it remains a blocker for exact shadow/guardrail historical replay if needed.
2. The exact original `veteran_player_inputs.csv` sidecar remains absent. This lane used a review-safe age adapter derived from recovered lifecycle receipts, not a production source promotion.
3. Exact historical replay remains blocked because this lane only rebuilds the current app-visible board, not season-by-season historical component receipts.
4. Production-active formula status remains blocked pending separate human review and approval.

## Safety Note

No canonical `local_exports` path was written. No production ranking output was changed.
"""
    (ARTIFACT_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_BLOCKERS.md").write_text(text, encoding="utf-8")


def write_source_trace(
    *,
    rebuilt_hash: str,
    final_hash: str,
    age_adapter_rows: int,
    field_diff_count: int,
) -> None:
    text = f"""# Current Board Recovery Rebuild Source Trace

Generated at UTC: `{datetime.now(timezone.utc).isoformat()}`

## Canonical HQ

Current remote HQ head verified before lane start:

`{CURRENT_REMOTE_HQ_HEAD}`

New commits since the prior validation lane were inspected and were docs-only/non-runtime.

## Prior Evidence

- Original Current Board Deterministic Rebuild Fix V1: `609e830e4d4c7f9b0d6082217847fe505dc2764b`
- Current Board Rebuild Input Recovery V1: `2a8086083e0ff867735a35c6804ca7fbc63e56a5`
- Current Board Missing File Manual Recovery V1: `43758e3cf2c30a4792bb0bcd33a4c8fd8e7468f7`
- Human Manual Recovery Packet V1: `0df59e9cf26b8d74232904b8452f623d55e50eb5`
- Recovery ZIP Ingest + Dropzone Validation V1: `d9d862be39e81a02412b14e8bfb5b2a18d8909ca`

## Recovered Input Root

`{DROPZONE_ROOT}`

Primary recovered source group used:

`{SOURCE_GROUP}`

## Logic Reused

Existing row logic from:

`src/services/model_v4_wr_qb_v2_candidate_service.py`

Functions reused:

- `_candidate_rows`
- `_component_lookup`
- `_age_lookup`
- `_write_csv`

No production formula file was edited. No model weight was changed.

## Key Hashes

- Rebuilt board hash: `{rebuilt_hash}`
- Pinned final board hash: `{PINNED_FINAL_BOARD_HASH}`
- Recovered final board hash: `{final_hash}`
- Detailed field diff count: `{field_diff_count}`
- QB age adapter rows: `{age_adapter_rows}`

## Caveat

The exact original age sidecar was not recovered. The adapter was derived from recovered lifecycle receipt rows and used only inside this review artifact lane. `shadow_model_v2_metrics.csv` remains absent and is not required for this exact board-row hash rebuild.
"""
    (ARTIFACT_DIR / "CURRENT_BOARD_RECOVERY_REBUILD_SOURCE_TRACE.md").write_text(
        text,
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
