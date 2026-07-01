from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

NOT_ENOUGH_INFORMATION = "Not enough information"

DEFAULT_OUTPUT_ROOT = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_stats_compact_sidecar_derivation_runner_v1_20260630"
)
DEFAULT_RECEIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_stats_row_level_source_admission_v1_20260630"
    / "player_stats_row_level_receipt.csv"
)
DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_stats_row_level_source_admission_v1_20260630"
    / "player_stats_schema_manifest.csv"
)
DEFAULT_PLAYER_CONTEXT_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "hq"
    / "data_sources"
    / "nflverse_player_context_display_20260630"
    / "nflverse_player_context_display_artifact.csv"
)

COMPACT_STAT_FIELDS = (
    "passing_first_downs",
    "rushing_first_downs",
    "receiving_first_downs",
)
QUARANTINED_NOTE_PATTERN = re.compile(r"quarantined_fields=([^;]+)")
SHA_NOTE_PATTERN = re.compile(r"sha256=([0-9a-fA-F]{64})")

CANDIDATE_FIELDS = [
    "sidecar_candidate_row_id",
    "source_dataset",
    "source_receipt_sha",
    "nwr_player_id",
    "nflverse_player_id",
    "gsis_id",
    "player_name",
    "position",
    "recent_team",
    "season",
    "week",
    "stat_family",
    "stat_name",
    "stat_value",
    "stat_unit",
    "source_as_of",
    "identity_join_status",
    "review_required",
    "sidecar_review_allowed",
    "label_truth_allowed",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "blocker_reason",
    "notes",
]

COVERAGE_FIELDS = [
    "source_dataset",
    "source_receipt_sha",
    "source_rows_expected",
    "source_rows_observed",
    "rows_derived",
    "seasons_covered",
    "weeks_covered",
    "positions_covered",
    "id_columns_used",
    "stat_fields_included",
    "quarantined_fields_excluded",
    "review_use_allowed",
    "sidecar_builder_allowed",
    "label_truth_allowed",
    "model_use_allowed",
    "training_allowed",
    "source_truth_allowed",
    "blocker_reason",
    "notes",
]


class CompactSidecarDerivationError(RuntimeError):
    pass


class ReceiptMismatchError(CompactSidecarDerivationError):
    pass


class LocalSnapshotUnavailableError(CompactSidecarDerivationError):
    pass


@dataclass(frozen=True)
class Receipt:
    source_dataset: str
    source_artifact: Path
    expected_rows: int
    expected_sha: str
    review_use_allowed: bool
    sidecar_builder_allowed: bool
    notes: str


@dataclass(frozen=True)
class DerivationResult:
    verdict: str
    candidate_rows: int
    receipts_validated: int
    weekly_rows_observed: int
    seasonal_rows_observed: int
    output_root: Path


def build_compact_sidecar_derivation_packet(
    *,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    receipt_path: Path = DEFAULT_RECEIPT_PATH,
    schema_path: Path = DEFAULT_SCHEMA_PATH,
    player_context_path: Path = DEFAULT_PLAYER_CONTEXT_PATH,
) -> DerivationResult:
    output_root.mkdir(parents=True, exist_ok=True)
    receipts = _load_receipts(receipt_path)
    schema_rows = _read_csv(schema_path)
    _validate_stat_fields(schema_rows)
    identity_map = _load_identity_map(player_context_path)

    coverage_rows: list[dict[str, str]] = []
    candidate_rows: list[dict[str, str]] = []
    validation_lines: list[str] = []
    receipt_count = 0
    weekly_rows_observed = 0
    seasonal_rows_observed = 0

    for receipt in receipts:
        if not receipt.review_use_allowed or not receipt.sidecar_builder_allowed:
            continue
        observed_rows = _validate_receipt(receipt)
        receipt_count += 1
        if receipt.source_dataset == "player_stats_weekly":
            weekly_rows_observed = observed_rows
            derived, coverage = _derive_weekly_candidates(receipt, identity_map)
            candidate_rows.extend(derived)
            coverage_rows.append(coverage)
        else:
            seasonal_rows_observed = observed_rows
            coverage_rows.append(
                _coverage_for_non_derived_receipt(receipt, observed_rows)
            )
        validation_message = (
            f"- `{receipt.source_dataset}`: row count `{observed_rows}` "
            f"and SHA `{receipt.expected_sha}` validated."
        )
        validation_lines.append(
            validation_message
        )

    if not candidate_rows:
        _write_blocked_packet(output_root, validation_lines)
        return DerivationResult(
            verdict="YELLOW_COMPACT_SIDECAR_DERIVATION_BLOCKED_SCHEMA_GAP",
            candidate_rows=0,
            receipts_validated=receipt_count,
            weekly_rows_observed=weekly_rows_observed,
            seasonal_rows_observed=seasonal_rows_observed,
            output_root=output_root,
        )

    _write_csv(
        output_root / "compact_player_stats_sidecar_candidate.csv",
        candidate_rows,
        CANDIDATE_FIELDS,
    )
    _write_csv(output_root / "derivation_coverage_matrix.csv", coverage_rows, COVERAGE_FIELDS)
    _write_schema(output_root / "compact_player_stats_sidecar_schema.csv")
    _write_success_reports(
        output_root=output_root,
        candidate_rows=candidate_rows,
        coverage_rows=coverage_rows,
        validation_lines=validation_lines,
        receipts_validated=receipt_count,
        weekly_rows_observed=weekly_rows_observed,
        seasonal_rows_observed=seasonal_rows_observed,
        receipt_path=receipt_path,
        schema_path=schema_path,
        player_context_path=player_context_path,
    )
    return DerivationResult(
        verdict="GREEN_COMPACT_SIDECAR_DERIVATION_READY_REVIEW_ONLY",
        candidate_rows=len(candidate_rows),
        receipts_validated=receipt_count,
        weekly_rows_observed=weekly_rows_observed,
        seasonal_rows_observed=seasonal_rows_observed,
        output_root=output_root,
    )


def _load_receipts(path: Path) -> list[Receipt]:
    rows = _read_csv(path)
    receipts: list[Receipt] = []
    for row in rows:
        expected_sha = _sha_from_notes(row.get("notes", ""))
        receipts.append(
            Receipt(
                source_dataset=row["source_dataset"],
                source_artifact=Path(row["source_artifact"]),
                expected_rows=int(row["row_count"]),
                expected_sha=expected_sha,
                review_use_allowed=row["review_use_allowed"] == "true",
                sidecar_builder_allowed=row["sidecar_builder_allowed"] == "true",
                notes=row.get("notes", ""),
            )
        )
    return receipts


def _validate_receipt(receipt: Receipt) -> int:
    if not receipt.source_artifact.exists():
        raise LocalSnapshotUnavailableError(
            f"local snapshot unavailable for {receipt.source_dataset}: {receipt.source_artifact}"
        )
    observed_sha = _sha256(receipt.source_artifact)
    if observed_sha != receipt.expected_sha:
        raise ReceiptMismatchError(
            f"SHA mismatch for {receipt.source_dataset}: "
            f"expected {receipt.expected_sha}, observed {observed_sha}"
        )
    observed_rows = _count_data_rows(receipt.source_artifact)
    if observed_rows != receipt.expected_rows:
        raise ReceiptMismatchError(
            f"row count mismatch for {receipt.source_dataset}: "
            f"expected {receipt.expected_rows}, observed {observed_rows}"
        )
    return observed_rows


def _derive_weekly_candidates(
    receipt: Receipt,
    identity_map: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, str]]:
    rows: list[dict[str, str]] = []
    seasons: set[str] = set()
    weeks: set[str] = set()
    positions: set[str] = set()
    source_rows_observed = 0
    matched_source_rows = 0

    with receipt.source_artifact.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"player_id", "player_name", "position", "season", "week", "team"}
        missing_required = sorted(required - set(reader.fieldnames or []))
        if missing_required:
            raise CompactSidecarDerivationError(
                f"{receipt.source_dataset} missing required columns: {', '.join(missing_required)}"
            )
        for source_row in reader:
            source_rows_observed += 1
            player_id = source_row.get("player_id", "")
            identity = identity_map.get(player_id)
            if not identity:
                continue
            matched_source_rows += 1
            season = _clean(source_row.get("season"))
            week = _clean(source_row.get("week"))
            position = _clean(source_row.get("position"))
            team = _clean(source_row.get("team"))
            seasons.add(season)
            weeks.add(week)
            positions.add(position)
            for stat_name in COMPACT_STAT_FIELDS:
                stat_value = _clean(source_row.get(stat_name))
                if not _is_nonzero_number(stat_value):
                    continue
                stat_family = stat_name.split("_", 1)[0]
                rows.append(
                    {
                        "sidecar_candidate_row_id": (
                            f"{receipt.source_dataset}__{season}__{week}__{player_id}__{stat_name}"
                        ),
                        "source_dataset": receipt.source_dataset,
                        "source_receipt_sha": receipt.expected_sha,
                        "nwr_player_id": identity["nwr_player_id"],
                        "nflverse_player_id": player_id,
                        "gsis_id": player_id,
                        "player_name": _clean(source_row.get("player_display_name"))
                        if _clean(source_row.get("player_display_name")) != NOT_ENOUGH_INFORMATION
                        else _clean(source_row.get("player_name")),
                        "position": position,
                        "recent_team": team,
                        "season": season,
                        "week": week,
                        "stat_family": stat_family,
                        "stat_name": stat_name,
                        "stat_value": stat_value,
                        "stat_unit": "count",
                        "source_as_of": NOT_ENOUGH_INFORMATION,
                        "identity_join_status": "SAFE_NOW_DISPLAY_ONLY",
                        "review_required": "false",
                        "sidecar_review_allowed": "true",
                        "label_truth_allowed": "false",
                        "model_use_allowed": "false",
                        "training_allowed": "false",
                        "source_truth_allowed": "false",
                        "blocker_reason": (
                            "No blocker for review-only compact candidate row; "
                            "label truth/model/training/source truth remain blocked."
                        ),
                        "notes": (
                            "Nonzero explicit first-down stat from admitted weekly "
                            "player_stats source. Absence from compact candidate is "
                            "not zero. Raw source remains local-only."
                        ),
                    }
                )

    coverage = {
        "source_dataset": receipt.source_dataset,
        "source_receipt_sha": receipt.expected_sha,
        "source_rows_expected": str(receipt.expected_rows),
        "source_rows_observed": str(source_rows_observed),
        "rows_derived": str(len(rows)),
        "seasons_covered": _range_or_nei(seasons),
        "weeks_covered": _range_or_nei(weeks),
        "positions_covered": "|".join(sorted(p for p in positions if p)) or NOT_ENOUGH_INFORMATION,
        "id_columns_used": "player_id|player_display_name|player_name|position|team|season|week",
        "stat_fields_included": "|".join(COMPACT_STAT_FIELDS),
        "quarantined_fields_excluded": "|".join(_quarantined_from_notes(receipt.notes)),
        "review_use_allowed": "true",
        "sidecar_builder_allowed": "true",
        "label_truth_allowed": "false",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "blocker_reason": (
            "No blocker for review-only compact derivation; "
            "replay/model/label truth remain blocked."
        ),
        "notes": (
            f"Matched identity-safe source rows={matched_source_rows}. "
            "Compact artifact emits nonzero first-down stats only."
        ),
    }
    return rows, coverage


def _coverage_for_non_derived_receipt(receipt: Receipt, observed_rows: int) -> dict[str, str]:
    return {
        "source_dataset": receipt.source_dataset,
        "source_receipt_sha": receipt.expected_sha,
        "source_rows_expected": str(receipt.expected_rows),
        "source_rows_observed": str(observed_rows),
        "rows_derived": "0",
        "seasons_covered": NOT_ENOUGH_INFORMATION,
        "weeks_covered": NOT_ENOUGH_INFORMATION,
        "positions_covered": NOT_ENOUGH_INFORMATION,
        "id_columns_used": "receipt validated only",
        "stat_fields_included": "none",
        "quarantined_fields_excluded": "|".join(_quarantined_from_notes(receipt.notes)),
        "review_use_allowed": "true",
        "sidecar_builder_allowed": "false",
        "label_truth_allowed": "false",
        "model_use_allowed": "false",
        "training_allowed": "false",
        "source_truth_allowed": "false",
        "blocker_reason": (
            "Seasonal receipt validated for provenance but compact V1 emits "
            "weekly row-level first-down candidates only."
        ),
        "notes": "No seasonal sidecar candidate rows emitted in V1.",
    }


def _load_identity_map(path: Path) -> dict[str, dict[str, str]]:
    rows = _read_csv(path)
    identity: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("identity_join_status") != "SAFE_NOW_DISPLAY_ONLY":
            continue
        if row.get("review_required") != "false":
            continue
        gsis_id = _clean(row.get("nflverse_gsis_id"))
        nwr_id = _clean(row.get("nwr_player_id"))
        if gsis_id == NOT_ENOUGH_INFORMATION or nwr_id == NOT_ENOUGH_INFORMATION:
            continue
        identity[gsis_id] = {"nwr_player_id": nwr_id}
    return identity


def _validate_stat_fields(schema_rows: list[dict[str, str]]) -> None:
    by_field = {row["field_name"]: row for row in schema_rows}
    missing = [field for field in COMPACT_STAT_FIELDS if field not in by_field]
    if missing:
        raise CompactSidecarDerivationError(
            f"compact stat fields missing from schema: {', '.join(missing)}"
        )
    blocked = [
        field
        for field in COMPACT_STAT_FIELDS
        if by_field[field].get("allowed_for_review") != "true"
    ]
    if blocked:
        raise CompactSidecarDerivationError(
            f"compact stat fields not allowed for review: {', '.join(blocked)}"
        )


def _write_schema(path: Path) -> None:
    rows = [
        {
            "column_name": field,
            "description": _candidate_description(field),
            "required": "true",
            "missingness_rule": (
                "Missing data remains Not enough information; absence from compact "
                "candidate is not zero."
            ),
            "label_truth_allowed": "false",
            "model_use_allowed": "false",
            "training_allowed": "false",
            "source_truth_allowed": "false",
            "notes": "Review-only compact sidecar candidate schema.",
        }
        for field in CANDIDATE_FIELDS
    ]
    _write_csv(
        path,
        rows,
        [
            "column_name",
            "description",
            "required",
            "missingness_rule",
            "label_truth_allowed",
            "model_use_allowed",
            "training_allowed",
            "source_truth_allowed",
            "notes",
        ],
    )


def _write_success_reports(
    *,
    output_root: Path,
    candidate_rows: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    validation_lines: list[str],
    receipts_validated: int,
    weekly_rows_observed: int,
    seasonal_rows_observed: int,
    receipt_path: Path,
    schema_path: Path,
    player_context_path: Path,
) -> None:
    stat_counts = Counter(row["stat_name"] for row in candidate_rows)
    position_counts = Counter(row["position"] for row in candidate_rows)
    season_values = {row["season"] for row in candidate_rows}
    week_values = {row["week"] for row in candidate_rows}
    source_sha = coverage_rows[0]["source_receipt_sha"] if coverage_rows else NOT_ENOUGH_INFORMATION
    quarantined = (
        coverage_rows[0]["quarantined_fields_excluded"].replace("|", ", ")
        if coverage_rows
        else NOT_ENOUGH_INFORMATION
    )

    _write(
        output_root / "artifact_manifest.md",
        f"""
# NFLVerse Player Stats Compact Sidecar Derivation Runner V1 Manifest

- verdict: `GREEN_COMPACT_SIDECAR_DERIVATION_READY_REVIEW_ONLY`
- service: `src/services/nflverse_player_stats_compact_sidecar_derivation_service.py`
- receipt_input: `{receipt_path}`
- schema_input: `{schema_path}`
- identity_input: `{player_context_path}`
- raw_source_tracked_in_git: `false`
- compact_candidate_rows: `{len(candidate_rows)}`
- receipts_validated: `{receipts_validated}`
- label_truth_allowed: `false`
- model_use_allowed: `false`
- training_allowed: `false`
- source_truth_allowed: `false`

## Outputs

- `compact_player_stats_sidecar_candidate.csv`
- `compact_player_stats_sidecar_schema.csv`
- `derivation_coverage_matrix.csv`
- `quarantined_fields_report.md`
- `source_receipt_validation_report.md`
- `sidecar_builder_handoff.md`
- `merge_safety_report.md`
""",
    )
    _write(
        output_root / "derivation_runner_summary.md",
        f"""
# Compact Sidecar Derivation Runner Summary

Verdict: `GREEN_COMPACT_SIDECAR_DERIVATION_READY_REVIEW_ONLY`

The non-runtime derivation service validated the admitted local-only NFLVerse
player_stats receipts and emitted a compact tracked review-only candidate
artifact.

## Counts

- Receipts validated: {receipts_validated}
- Weekly source rows observed: {weekly_rows_observed}
- Seasonal source rows observed: {seasonal_rows_observed}
- Compact candidate rows: {len(candidate_rows)}
- Seasons covered in candidate: {_range_or_nei(season_values)}
- Weeks covered in candidate: {_range_or_nei(week_values)}
- Positions covered in candidate: {', '.join(sorted(position_counts)) or NOT_ENOUGH_INFORMATION}

## Stat Families

{_markdown_counter(stat_counts)}

## Boundary

Candidate rows are comparison substrate only. They are not labels, model
features, training inputs, source truth, rank logic, hidden sort,
recommendations, trade value, or pick value.
""",
    )
    _write(
        output_root / "quarantined_fields_report.md",
        f"""
# Quarantined Fields Report

The compact derivation excludes every quarantined field from the admitted source receipt.

## Excluded Fields

`{quarantined}`

## Included Fields

`{', '.join(COMPACT_STAT_FIELDS)}`

The included fields are review-allowed in the source-admission schema manifest.
Quarantined fields remain blocked from review sidecar rows, private value,
hidden sort, model, training, source truth, recommendations, trade value,
and pick value.
""",
    )
    _write(
        output_root / "source_receipt_validation_report.md",
        "# Source Receipt Validation Report\n\n" + "\n".join(validation_lines),
    )
    _write(
        output_root / "sidecar_builder_handoff.md",
        f"""
# Sidecar Builder Handoff

Status: `COMPACT_SIDECAR_CANDIDATE_READY_REVIEW_ONLY`

Future sidecar builder lanes may consume:

- `compact_player_stats_sidecar_candidate.csv`
- `compact_player_stats_sidecar_schema.csv`
- `derivation_coverage_matrix.csv`

Required filters:

- `sidecar_review_allowed=true`
- `identity_join_status=SAFE_NOW_DISPLAY_ONLY`
- `review_required=false`
- `label_truth_allowed=false`
- `model_use_allowed=false`
- `training_allowed=false`
- `source_truth_allowed=false`

Source receipt SHA used for weekly candidates: `{source_sha}`.

Absence from the compact candidate file is not zero production. V1 emits
explicit nonzero first-down stats only.
""",
    )
    _write(
        output_root / "merge_safety_report.md",
        """
# Merge Safety Report

## Scope

Non-runtime service, tests, and compact docs/CSV derivation artifact only.

## Confirmed Guardrails

- No app behavior changed.
- No model, rank, source-truth, Outcome, Rookie, Trading Lab, Player Compare,
  Draft Room, latest pointer, or protected artifact files changed.
- No raw/shared/cache/local_exports/private/vendor/Gmail/secret/runtime JSON files were tracked.
- No label truth, model input, training input, source truth, rank logic,
  hidden sort, recommendation, trade value, or pick value approval was granted.
- No experiments, simulations, probabilities, or model training were run.
""",
    )


def _write_blocked_packet(output_root: Path, validation_lines: list[str]) -> None:
    _write(
        output_root / "blocked_derivation_report.md",
        "# Blocked Derivation Report\n\n"
        "Verdict: `YELLOW_COMPACT_SIDECAR_DERIVATION_BLOCKED_SCHEMA_GAP`\n\n"
        "The receipt validation succeeded, but no compact sidecar candidate rows were emitted. "
        "Do not fake data.\n\n"
        + "\n".join(validation_lines),
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, NOT_ENOUGH_INFORMATION) for field in fields})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _count_data_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def _sha_from_notes(notes: str) -> str:
    match = SHA_NOTE_PATTERN.search(notes)
    if not match:
        raise CompactSidecarDerivationError("receipt notes missing sha256")
    return match.group(1).lower()


def _quarantined_from_notes(notes: str) -> tuple[str, ...]:
    match = QUARANTINED_NOTE_PATTERN.search(notes)
    if not match:
        return ()
    return tuple(field.strip() for field in match.group(1).split("|") if field.strip())


def _clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return text if text else NOT_ENOUGH_INFORMATION


def _is_nonzero_number(value: str) -> bool:
    try:
        return float(value) != 0.0
    except ValueError:
        return False


def _range_or_nei(values: set[str]) -> str:
    clean_values = sorted(v for v in values if v and v != NOT_ENOUGH_INFORMATION)
    if not clean_values:
        return NOT_ENOUGH_INFORMATION
    numeric = sorted(int(v) for v in clean_values if v.isdigit())
    if numeric and len(numeric) == len(clean_values):
        return f"{numeric[0]}-{numeric[-1]}" if numeric[0] != numeric[-1] else str(numeric[0])
    return "|".join(clean_values)


def _candidate_description(field: str) -> str:
    descriptions = {
        "sidecar_candidate_row_id": "Deterministic candidate row id.",
        "source_dataset": "Admitted NFLVerse source dataset.",
        "source_receipt_sha": "Validated SHA-256 from source admission receipt.",
        "nwr_player_id": "NWR player id from safe player context identity join.",
        "nflverse_player_id": "NFLVerse player id from player_stats source row.",
        "gsis_id": "GSIS id, equal to player_stats player_id for this source.",
        "stat_value": "Explicit nonzero stat value from source row.",
        "source_as_of": "Source as-of timestamp; Not enough information for this packet.",
    }
    return descriptions.get(field, "Review-only compact sidecar candidate field.")


def _markdown_counter(counter: Counter[str]) -> str:
    if not counter:
        return "- Not enough information"
    return "\n".join(f"- `{key}`: {value}" for key, value in sorted(counter.items()))
