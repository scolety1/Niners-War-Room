from __future__ import annotations

import csv
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.services.draft_state_service import create_empty_draft_state
from src.services.mock_draft_combined_state_service import CombinedSimulatorState
from src.services.mock_draft_run_report_service import build_mock_draft_run_report
from src.services.mock_draft_simulator_service import (
    BLOCKED_MARKET_SCORE_FIELDS,
    build_review_mock_draft_scenario,
)

DEFAULT_FAKE_MARKET_TIMING_FIXTURE = Path(
    "tests/fixtures/mock_draft/fake_market_timing_rows.csv"
)
DEFAULT_FAKE_MARKET_TIMING_DRY_RUN_OUTPUT_ROOT = Path(
    "local_exports/mock_draft/fake_market_timing_dry_run_20260616"
)

APPROVED_BEHAVIOR_COLUMNS = frozenset(
    {
        "asset_id",
        "player",
        "position",
        "source_name",
        "source_type",
        "source_timestamp",
        "market_adp",
        "overall_adp",
        "expected_pick",
        "adp_min",
        "adp_max",
        "sample_size",
        "league_format_note",
        "identity_match_method",
        "review_flags",
    }
)
FROZEN_ROOKIE_GUIDANCE_FIELDS = (
    "rank",
    "tier",
    "draft_action",
    "warning_severity",
    "draft_room_note",
)
FAKE_SOURCE_NAME = "fake_contract_fixture"
FAKE_SOURCE_TYPE = "synthetic_market_timing"

VALIDATION_COLUMNS = (
    "asset_id",
    "player",
    "source_name",
    "source_type",
    "has_behavior_timing",
    "allowed_for_behavior",
    "blocked_score_fields_ignored",
    "disallowed_columns_flagged",
    "review_flags",
    "validation_status",
)
BEHAVIOR_NOTE_COLUMNS = (
    "note_type",
    "overall_pick",
    "pick_label",
    "baseline_selected_player",
    "fake_market_selected_player",
    "availability_changed",
    "market_context_used",
    "note",
)
CONTAMINATION_COLUMNS = (
    "check_name",
    "passed",
    "detail",
)


@dataclass(frozen=True)
class FakeMarketTimingDryRun:
    review_only: bool
    fixture_path: Path
    fixture_row_count: int
    validation_rows: tuple[dict[str, object], ...]
    behavior_notes: tuple[dict[str, object], ...]
    contamination_checks: tuple[dict[str, object], ...]
    manifest: dict[str, object]
    artifact_paths: dict[str, Path]


def read_fake_market_timing_rows(
    fixture_path: str | Path = DEFAULT_FAKE_MARKET_TIMING_FIXTURE,
) -> tuple[dict[str, str], ...]:
    path = Path(fixture_path)
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(csv.DictReader(handle))


def validate_fake_market_timing_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    validation_rows: list[dict[str, object]] = []
    for row in rows:
        blocked = _populated_columns(row, BLOCKED_MARKET_SCORE_FIELDS)
        disallowed = _populated_columns(
            row,
            set(row) - APPROVED_BEHAVIOR_COLUMNS - BLOCKED_MARKET_SCORE_FIELDS,
        )
        flags = _row_review_flags(row, blocked=blocked, disallowed=disallowed)
        allowed_for_behavior = _is_fake_source(row) and _has_behavior_timing(row)
        if disallowed:
            status = "flagged_disallowed_columns"
        elif blocked:
            status = "valid_behavior_only_with_ignored_score_fields"
        elif allowed_for_behavior:
            status = "valid_behavior_only"
        else:
            status = "review_required_behavior_fallback"
        validation_rows.append(
            {
                "asset_id": row.get("asset_id") or "",
                "player": row.get("player") or "",
                "source_name": row.get("source_name") or "",
                "source_type": row.get("source_type") or "",
                "has_behavior_timing": _has_behavior_timing(row),
                "allowed_for_behavior": allowed_for_behavior,
                "blocked_score_fields_ignored": "|".join(blocked),
                "disallowed_columns_flagged": "|".join(disallowed),
                "review_flags": "|".join(flags),
                "validation_status": status,
            }
        )
    return tuple(validation_rows)


def behavior_only_market_context_rows(
    rows: Sequence[Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    validation_by_asset = {
        str(row["asset_id"]): row for row in validate_fake_market_timing_rows(rows)
    }
    context_rows: list[dict[str, object]] = []
    for row in rows:
        asset_id = str(row.get("asset_id") or "")
        validation = validation_by_asset.get(asset_id, {})
        if not validation.get("allowed_for_behavior"):
            continue
        context_rows.append(
            {
                "asset_id": asset_id,
                "player": row.get("player") or "",
                "market_adp": row.get("market_adp") or row.get("overall_adp") or "",
                "expected_pick": row.get("expected_pick") or "",
                "source": row.get("source_name") or FAKE_SOURCE_NAME,
            }
        )
    return tuple(context_rows)


def build_fake_market_timing_dry_run(
    *,
    fixture_path: str | Path = DEFAULT_FAKE_MARKET_TIMING_FIXTURE,
) -> FakeMarketTimingDryRun:
    fixture = Path(fixture_path)
    fake_rows = read_fake_market_timing_rows(fixture)
    validation_rows = validate_fake_market_timing_rows(fake_rows)
    behavior_rows = behavior_only_market_context_rows(fake_rows)

    baseline = build_review_mock_draft_scenario(
        create_empty_draft_state(
            pick_rows=_dry_run_pick_rows(),
            available_rows=_draft_state_available_rows(),
        ),
        market_context_rows=(),
        opponent_lookahead=2,
    )
    with_market = build_review_mock_draft_scenario(
        create_empty_draft_state(
            pick_rows=_dry_run_pick_rows(),
            available_rows=_draft_state_available_rows(),
        ),
        market_context_rows=behavior_rows,
        opponent_lookahead=2,
    )
    report = build_mock_draft_run_report(
        _dry_run_combined_state(),
        market_context_rows=behavior_rows,
        shortlist_size=3,
        opponent_lookahead=2,
    )
    behavior_notes = _behavior_notes(baseline=baseline, with_market=with_market)
    contamination_checks = _contamination_checks(report=report, with_market=with_market)
    manifest = _manifest(
        fixture=fixture,
        fixture_rows=fake_rows,
        validation_rows=validation_rows,
        behavior_notes=behavior_notes,
        contamination_checks=contamination_checks,
    )
    return FakeMarketTimingDryRun(
        review_only=True,
        fixture_path=fixture,
        fixture_row_count=len(fake_rows),
        validation_rows=validation_rows,
        behavior_notes=behavior_notes,
        contamination_checks=contamination_checks,
        manifest=manifest,
        artifact_paths={},
    )


def write_fake_market_timing_dry_run_artifacts(
    dry_run: FakeMarketTimingDryRun,
    *,
    output_root: str | Path = DEFAULT_FAKE_MARKET_TIMING_DRY_RUN_OUTPUT_ROOT,
) -> FakeMarketTimingDryRun:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    validation_path = root / "fake_market_timing_validation_rows.csv"
    notes_path = root / "fake_market_timing_behavior_notes.csv"
    contamination_path = root / "fake_market_timing_contamination_check.csv"
    manifest_path = root / "fake_market_timing_dry_run_manifest.json"
    _write_csv(validation_path, VALIDATION_COLUMNS, dry_run.validation_rows)
    _write_csv(notes_path, BEHAVIOR_NOTE_COLUMNS, dry_run.behavior_notes)
    _write_csv(contamination_path, CONTAMINATION_COLUMNS, dry_run.contamination_checks)
    manifest = {
        **dry_run.manifest,
        "artifact_paths": {
            "validation_rows": str(validation_path),
            "behavior_notes": str(notes_path),
            "contamination_check": str(contamination_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return FakeMarketTimingDryRun(
        review_only=dry_run.review_only,
        fixture_path=dry_run.fixture_path,
        fixture_row_count=dry_run.fixture_row_count,
        validation_rows=dry_run.validation_rows,
        behavior_notes=dry_run.behavior_notes,
        contamination_checks=dry_run.contamination_checks,
        manifest=manifest,
        artifact_paths={
            "validation_rows": validation_path,
            "behavior_notes": notes_path,
            "contamination_check": contamination_path,
            "manifest": manifest_path,
        },
    )


def build_and_write_fake_market_timing_dry_run(
    *,
    fixture_path: str | Path = DEFAULT_FAKE_MARKET_TIMING_FIXTURE,
    output_root: str | Path = DEFAULT_FAKE_MARKET_TIMING_DRY_RUN_OUTPUT_ROOT,
) -> FakeMarketTimingDryRun:
    return write_fake_market_timing_dry_run_artifacts(
        build_fake_market_timing_dry_run(fixture_path=fixture_path),
        output_root=output_root,
    )


def _row_review_flags(
    row: Mapping[str, object],
    *,
    blocked: tuple[str, ...],
    disallowed: tuple[str, ...],
) -> tuple[str, ...]:
    flags = [
        flag for flag in str(row.get("review_flags") or "").split("|") if flag
    ]
    if not _is_fake_source(row):
        flags.append("non_fake_market_source_rejected")
    if not _has_behavior_timing(row):
        flags.append("market_timing_missing_pick_value_review_required")
    if blocked:
        flags.append("market_score_fields_ignored")
    if disallowed:
        flags.append("market_timing_disallowed_columns_review_required")
    return tuple(dict.fromkeys(flags))


def _populated_columns(
    row: Mapping[str, object],
    columns: set[str] | frozenset[str],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            column
            for column in columns
            if column in row and row.get(column) not in (None, "")
        )
    )


def _is_fake_source(row: Mapping[str, object]) -> bool:
    return (
        str(row.get("source_name") or "") == FAKE_SOURCE_NAME
        and str(row.get("source_type") or "") == FAKE_SOURCE_TYPE
    )


def _has_behavior_timing(row: Mapping[str, object]) -> bool:
    return any(
        row.get(column) not in (None, "")
        for column in ("market_adp", "overall_adp", "expected_pick")
    )


def _behavior_notes(*, baseline: object, with_market: object) -> tuple[dict[str, object], ...]:
    baseline_pick = baseline.simulated_picks[0] if baseline.simulated_picks else None
    market_pick = with_market.simulated_picks[0] if with_market.simulated_picks else None
    baseline_available = {
        row["asset_id"] for row in baseline.availability_at_my_next_pick
    }
    market_available = {
        row["asset_id"] for row in with_market.availability_at_my_next_pick
    }
    availability_changed = baseline_available != market_available
    return (
        {
            "note_type": "opponent_timing_changed",
            "overall_pick": market_pick.overall_pick if market_pick else "",
            "pick_label": market_pick.pick_label if market_pick else "",
            "baseline_selected_player": baseline_pick.player if baseline_pick else "",
            "fake_market_selected_player": market_pick.player if market_pick else "",
            "availability_changed": availability_changed,
            "market_context_used": bool(market_pick and market_pick.market_adp is not None),
            "note": (
                "Fake market timing changed opponent behavior only; NWR value and "
                "rookie guidance remained unchanged."
            ),
        },
        {
            "note_type": "availability_notes_changed",
            "overall_pick": "",
            "pick_label": "",
            "baseline_selected_player": "",
            "fake_market_selected_player": "",
            "availability_changed": availability_changed,
            "market_context_used": True,
            "note": (
                "Availability at the next Tim/Niners window changed because the "
                "fake market-timed opponent pick removed a different player."
            ),
        },
    )


def _contamination_checks(*, report: object, with_market: object) -> tuple[dict[str, object], ...]:
    beta = next(row for row in report.tim_shortlist_rows if row["player"] == "Beta Rookie")
    free_agent = next(row for row in report.tim_shortlist_rows if row["player"] == "Bench RB")
    checks = (
        (
            "opponent_behavior_changed",
            with_market.simulated_picks[0].player == "Steady Released WR",
            "Fake timing selected Steady Released WR at opponent pick 1.",
        ),
        (
            "rookie_guidance_unchanged",
            all(
                (
                    beta["rank"] == "2",
                    beta["tier"] == "Tier 2",
                    beta["draft_action"] == "manual_review",
                    beta["warning_severity"] == "yellow",
                )
            ),
            "Frozen rookie guidance copied through unchanged.",
        ),
        (
            "no_numeric_nwr_score_created",
            beta["stats_model_value"] == 0.0
            and "No numeric NWR score is invented" in report.manifest["nwr_score_policy"],
            "No numeric NWR score was created from fake timing.",
        ),
        (
            "value_neutral_flags_preserved",
            free_agent["value_status"] == "value_neutral"
            and "value_neutral" in str(free_agent["review_flags"]),
            "Value-neutral free agent flags remained intact.",
        ),
        (
            "market_behavior_only",
            report.manifest["market_context_rows"] == 2
            and "behavior-only" in report.manifest["market_adp_policy"],
            "Fake market rows entered only opponent timing context.",
        ),
        (
            "no_real_market_data_required",
            True,
            "Dry run uses only tests/fixtures/mock_draft/fake_market_timing_rows.csv.",
        ),
    )
    return tuple(
        {"check_name": name, "passed": passed, "detail": detail}
        for name, passed, detail in checks
    )


def _manifest(
    *,
    fixture: Path,
    fixture_rows: tuple[dict[str, str], ...],
    validation_rows: tuple[dict[str, object], ...],
    behavior_notes: tuple[dict[str, object], ...],
    contamination_checks: tuple[dict[str, object], ...],
) -> dict[str, object]:
    flag_counts: Counter[str] = Counter()
    for row in validation_rows:
        for flag in str(row.get("review_flags") or "").split("|"):
            if flag:
                flag_counts[flag] += 1
    return {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "review_only": True,
        "fixture_path": str(fixture),
        "fixture_policy": "fake_fixture_only_no_real_market_data_imported",
        "fixture_rows": len(fixture_rows),
        "validation_rows": len(validation_rows),
        "behavior_only_rows": sum(
            1 for row in validation_rows if row.get("allowed_for_behavior")
        ),
        "behavior_note_rows": len(behavior_notes),
        "contamination_check_rows": len(contamination_checks),
        "contamination_checks_passed": sum(
            1 for row in contamination_checks if row.get("passed")
        ),
        "review_flags": dict(sorted(flag_counts.items())),
        "market_policy": (
            "Fake ADP/market timing may affect opponent behavior, likely pick timing, "
            "availability notes, and behavior-only scenario outputs only."
        ),
        "nwr_score_policy": (
            "Fake ADP/market timing cannot enter NWR private value, alter frozen rookie "
            "guidance, backfill missing scores, create numeric scores, or remove "
            "value-neutral flags."
        ),
        "promotion_status": "local_dry_run_output_only_not_app_wired_not_promoted",
    }


def _dry_run_pick_rows() -> list[dict[str, object]]:
    return [
        {
            "overall_pick": 1,
            "round": 1,
            "round_pick": 1,
            "pick_label": "1.01",
            "current_owner": "Opponent",
            "original_owner": "Opponent",
            "is_my_pick": False,
        },
        {
            "overall_pick": 2,
            "round": 1,
            "round_pick": 2,
            "pick_label": "1.02",
            "current_owner": "Niners",
            "original_owner": "Niners",
            "is_my_pick": True,
        },
    ]


def _draft_state_available_rows() -> list[dict[str, object]]:
    return [
        {
            "asset_id": "rookie:alpha_wr",
            "player": "Alpha WR",
            "position": "WR",
            "nfl_team": "Rookie Pool",
            "asset_type": "Rookie",
            "asset_lifecycle": "incoming_rookie",
            "stats_model_value": 91.0,
            "market_value": 0.0,
            "market_edge": 0.0,
            "confidence": 88.0,
            "overall_rank": 1,
        },
        {
            "asset_id": "released_veteran:steady_wr",
            "player": "Steady Released WR",
            "position": "WR",
            "nfl_team": "FA",
            "asset_type": "Released Veteran",
            "asset_lifecycle": "dropped_veteran",
            "stats_model_value": 74.0,
            "market_value": 0.0,
            "market_edge": 0.0,
            "confidence": 80.0,
            "overall_rank": 5,
        },
        {
            "asset_id": "free_agent:bench_rb",
            "player": "Bench RB",
            "position": "RB",
            "nfl_team": "FA",
            "asset_type": "Free Agent",
            "asset_lifecycle": "free_agent",
            "stats_model_value": 69.0,
            "market_value": 0.0,
            "market_edge": 0.0,
            "confidence": 70.0,
            "overall_rank": 7,
        },
    ]


def _dry_run_combined_state() -> CombinedSimulatorState:
    return CombinedSimulatorState(
        review_only=True,
        available_rows=(
            {
                "asset_id": "frozen_rookie:alpha:rank1",
                "player": "Alpha Rookie",
                "position": "RB",
                "source_label": "frozen_rookie",
                "draft_rank": 1,
                "stats_model_value": 0.0,
                "rank": "1",
                "tier": "Tier 1",
                "draft_action": "priority_review",
                "warning_severity": "green",
                "draft_room_note": "Frozen note",
                "review_flags": "frozen_rookie_guidance_read_only",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
            },
            {
                "asset_id": "rookie:beta_wr",
                "player": "Beta Rookie",
                "position": "WR",
                "source_label": "frozen_rookie",
                "draft_rank": 2,
                "stats_model_value": 0.0,
                "rank": "2",
                "tier": "Tier 2",
                "draft_action": "manual_review",
                "warning_severity": "yellow",
                "draft_room_note": "Frozen second note",
                "review_flags": "frozen_rookie_guidance_read_only",
                "nwr_score_status": "no_numeric_score_exposed_guidance_only",
                "value_status": "frozen_rookie_guidance_no_numeric_score",
            },
            {
                "asset_id": "free_agent:bench_rb",
                "player": "Bench RB",
                "position": "RB",
                "source_label": "free_agent",
                "draft_rank": 115,
                "stats_model_value": 0.0,
                "rank": "",
                "tier": "",
                "draft_action": "",
                "warning_severity": "",
                "draft_room_note": "",
                "review_flags": "value_neutral|free_agent",
                "nwr_score_status": "not_populated_from_snapshot_rank",
                "value_status": "value_neutral",
            },
        ),
        pick_rows=(
            {
                "overall_pick": 1,
                "round": 1,
                "round_pick": 1,
                "pick_label": "1.01",
                "current_owner": "Other",
                "manager": "Other Manager",
                "is_my_pick": False,
            },
            {
                "overall_pick": 2,
                "round": 1,
                "round_pick": 2,
                "pick_label": "1.02",
                "current_owner": "Niners",
                "manager": "Mike Colety",
                "is_my_pick": True,
            },
        ),
        draft_state=None,
        manifest={},
        review_flags={},
        source_counts={"frozen_rookie": 2, "free_agent": 1},
        artifact_paths={},
    )


def _write_csv(
    path: Path,
    fieldnames: tuple[str, ...],
    rows: tuple[dict[str, object], ...],
) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
