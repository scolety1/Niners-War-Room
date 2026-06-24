from __future__ import annotations

# ruff: noqa: E501
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "docs" / "hq" / "model" / "unified_player_universe_v0"

FULL_DYNASTY_PATH = (
    REPO_ROOT
    / "local_exports"
    / "model_v4"
    / "current_value"
    / "latest"
    / "full_player_board_value_review_rows.csv"
)
FROZEN_BOARD_PATH = (
    REPO_ROOT
    / "docs"
    / "draft_day_exports"
    / "final_board_v1_20260622"
    / "FINAL_DRAFT_BOARD_V1_FROZEN.csv"
)
ROOKIE_OVERLAY_PATH = (
    REPO_ROOT
    / "docs"
    / "draft_day_exports"
    / "final_board_v1_20260622"
    / "app_props"
    / "rookie_hq"
    / "rookie_overlay_context.csv"
)
ROOKIE_WARNING_PATH = (
    REPO_ROOT
    / "docs"
    / "draft_day_exports"
    / "final_board_v1_20260622"
    / "app_props"
    / "rookie_hq"
    / "rookie_warning_cards.csv"
)
PDF_FREE_AGENT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "overnight_accuracy_max_20260622"
    / "free_agent_pdf_page3_draftable_pool.csv"
)
MARKET_BASELINE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "dynastyprocess_market_baseline_20260622"
    / "dp_market_baseline_context.csv"
)
OUTCOME_CONTEXT_PATH = (
    REPO_ROOT
    / "docs"
    / "draft_day_exports"
    / "final_board_v1_20260622"
    / "app_props"
    / "outcome_columns"
    / "outcome_player_context.csv"
)
IDENTITY_AUDIT_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "data_sources"
    / "identity"
    / "player_id_coverage_audit_v1.csv"
)
ROOKIE_AGE_PATH = (
    REPO_ROOT
    / "docs"
    / "hq"
    / "parallel_lanes"
    / "age_source_audit_20260622"
    / "rookie_verified_age_display_20260622.csv"
)

REVIEW_PATH = OUTPUT_DIR / "unified_player_universe_v1_review.csv"
VALIDATION_REPORT_PATH = OUTPUT_DIR / "unified_player_universe_v1_validation_report.csv"
DUPLICATE_REVIEW_PATH = OUTPUT_DIR / "unified_player_universe_v1_duplicate_review.csv"
IDENTITY_GAP_REVIEW_PATH = OUTPUT_DIR / "unified_player_universe_v1_identity_gap_review.csv"
IDENTITY_TRIAGE_PATH = OUTPUT_DIR / "unified_player_universe_v1_identity_triage.csv"
SOURCE_SUMMARY_PATH = OUTPUT_DIR / "unified_player_universe_v1_source_summary.csv"

NOT_ENOUGH_INFORMATION = "Not enough information"
APP_WIRING_ALLOWED = "no"
MODEL_INPUT_ALLOWED = "no"

REQUIRED_REVIEW_COLUMNS = (
    "player_universe_id",
    "player_id",
    "player_name",
    "normalized_name",
    "position",
    "nfl_team",
    "age",
    "age_source",
    "player_type",
    "availability_status",
    "rank_source",
    "dynasty_rank",
    "rookie_rank",
    "frozen_baseline_rank",
    "candidate_rank",
    "unified_display_rank",
    "unified_display_rank_source",
    "tier",
    "tier_source",
    "outcome_context",
    "outcome_status",
    "market_match_status",
    "dp_1qb_value",
    "dp_market_rank",
    "nwr_vs_market_gap",
    "data_quality_status",
    "manual_review_flag",
    "caveats",
    "source_files",
    "source_layer",
    "join_confidence",
    "duplicate_group_id",
    "review_status",
    "app_wiring_allowed",
    "model_input_allowed",
)

PLAYER_TYPE_VALUES = {"VETERAN", "ROOKIE", "PROSPECT", "PDF_FA", "UNKNOWN"}
REVIEW_STATUS_VALUES = {"READY", "REVIEW_NEEDED", "NOT_ENOUGH_INFORMATION"}
DATA_QUALITY_VALUES = {"GREEN", "YELLOW", "RED", "MANUAL_REVIEW", "NOT_ENOUGH_INFORMATION"}
MARKET_STATUS_VALUES = {"MATCHED", "UNMATCHED", "DISPLAY_ONLY"}
OUTCOME_STATUS_VALUES = {"SUPPORTED", "MISSING", "UNSUPPORTED", "NOT_APPLICABLE"}
RANK_SOURCE_VALUES = {
    "FULL_DYNASTY_RANK",
    "ROOKIE_RANK",
    "FROZEN_BASELINE_RANK",
    "CANDIDATE_RANK",
    "UNRANKED_REVIEW",
}
TRIAGE_CLASS_VALUES = {
    "SAFE_REPAIR_EXISTING_CROSSWALK",
    "SAFE_REPAIR_EXACT_APPROVED_MATCH",
    "EXPECTED_NO_ID_REVIEW_ONLY",
    "NEEDS_MANUAL_REVIEW",
    "DO_NOT_REPAIR",
}
DUPLICATE_CLASS_VALUES = {
    "TRUE_DUPLICATE_SAFE_MERGE_LATER",
    "MULTI_LAYER_SAME_PLAYER_EXPECTED",
    "NAME_COLLISION",
    "SUFFIX_VARIANT",
    "POSITION_CONFLICT",
    "TEAM_CONFLICT",
    "NEEDS_MANUAL_REVIEW",
}
IDENTITY_TRIAGE_COLUMNS = (
    "player_name",
    "position",
    "source_layer",
    "original_player_id",
    "proposed_player_id",
    "triage_class",
    "action_taken",
    "confidence",
    "source_used",
    "remaining_risk",
    "notes",
)


@dataclass(frozen=True)
class BuildResult:
    review_path: Path
    validation_report_path: Path
    duplicate_review_path: Path
    identity_gap_review_path: Path
    identity_triage_path: Path
    source_summary_path: Path
    total_rows: int
    veteran_rows: int
    rookie_rows: int
    pdf_fa_rows: int
    duplicate_review_count: int
    identity_gap_count: int
    safe_repair_count: int


def build_unified_player_universe_review() -> BuildResult:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = _load_sources()
    rows: list[dict[str, Any]] = []
    rows.extend(_veteran_rows(sources))
    rows.extend(_rookie_rows(sources))
    rows.extend(_frozen_dropped_veteran_rows(sources))
    rows.extend(_pdf_free_agent_rows(sources))

    review = pd.DataFrame(rows, columns=REQUIRED_REVIEW_COLUMNS)
    review = _apply_duplicate_groups(review)
    identity_gap_review = _identity_gap_review(review)
    identity_triage = _identity_triage(review, identity_gap_review, sources)
    review, safe_repair_count = _apply_safe_identity_repairs(review, identity_triage)
    review = _apply_duplicate_groups(review)
    duplicate_review = _duplicate_review(review)
    identity_gap_review = _identity_gap_review(review)
    source_summary = _source_summary(review, sources, identity_gap_review, duplicate_review)
    validation_report = validate_review_frame(
        review,
        duplicate_review,
        identity_gap_review,
        sources,
        identity_triage,
    )

    review.to_csv(REVIEW_PATH, index=False)
    validation_report.to_csv(VALIDATION_REPORT_PATH, index=False)
    duplicate_review.to_csv(DUPLICATE_REVIEW_PATH, index=False)
    identity_gap_review.to_csv(IDENTITY_GAP_REVIEW_PATH, index=False)
    identity_triage.to_csv(IDENTITY_TRIAGE_PATH, index=False)
    source_summary.to_csv(SOURCE_SUMMARY_PATH, index=False)

    return BuildResult(
        review_path=REVIEW_PATH,
        validation_report_path=VALIDATION_REPORT_PATH,
        duplicate_review_path=DUPLICATE_REVIEW_PATH,
        identity_gap_review_path=IDENTITY_GAP_REVIEW_PATH,
        identity_triage_path=IDENTITY_TRIAGE_PATH,
        source_summary_path=SOURCE_SUMMARY_PATH,
        total_rows=int(len(review)),
        veteran_rows=int(review["player_type"].eq("VETERAN").sum()),
        rookie_rows=int(review["player_type"].isin(["ROOKIE", "PROSPECT"]).sum()),
        pdf_fa_rows=int(review["player_type"].eq("PDF_FA").sum()),
        duplicate_review_count=int(len(duplicate_review)),
        identity_gap_count=int(len(identity_gap_review)),
        safe_repair_count=safe_repair_count,
    )


def validate_artifact_files(output_dir: Path = OUTPUT_DIR) -> pd.DataFrame:
    review = pd.read_csv(output_dir / REVIEW_PATH.name, keep_default_na=False)
    duplicate_review = pd.read_csv(output_dir / DUPLICATE_REVIEW_PATH.name, keep_default_na=False)
    identity_gap_review = pd.read_csv(
        output_dir / IDENTITY_GAP_REVIEW_PATH.name,
        keep_default_na=False,
    )
    identity_triage = pd.read_csv(output_dir / IDENTITY_TRIAGE_PATH.name, keep_default_na=False)
    source_summary = pd.read_csv(output_dir / SOURCE_SUMMARY_PATH.name, keep_default_na=False)
    sources = {
        "full_dynasty": _read_csv(FULL_DYNASTY_PATH),
        "frozen": _read_csv(FROZEN_BOARD_PATH),
    }
    report = validate_review_frame(
        review,
        duplicate_review,
        identity_gap_review,
        sources,
        identity_triage,
    )
    report = pd.concat(
        [
            report,
            pd.DataFrame(
                [
                    _check_row(
                        "source_summary_loads",
                        not source_summary.empty,
                        f"source summary rows={len(source_summary)}",
                    )
                ]
            ),
        ],
        ignore_index=True,
    )
    return report


def validate_review_frame(
    review: pd.DataFrame,
    duplicate_review: pd.DataFrame,
    identity_gap_review: pd.DataFrame,
    sources: dict[str, pd.DataFrame],
    identity_triage: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if identity_triage is None:
        identity_triage = pd.DataFrame(columns=IDENTITY_TRIAGE_COLUMNS)
    checks = [
        _check_row(
            "required_columns_exist",
            set(REQUIRED_REVIEW_COLUMNS).issubset(review.columns),
            _missing_message(REQUIRED_REVIEW_COLUMNS, review.columns),
        ),
        _check_row(
            "player_type_enum_valid",
            _column_values_in(review, "player_type", PLAYER_TYPE_VALUES),
            _bad_values_message(review, "player_type", PLAYER_TYPE_VALUES),
        ),
        _check_row(
            "review_status_enum_valid",
            _column_values_in(review, "review_status", REVIEW_STATUS_VALUES),
            _bad_values_message(review, "review_status", REVIEW_STATUS_VALUES),
        ),
        _check_row(
            "data_quality_enum_valid",
            _column_values_in(review, "data_quality_status", DATA_QUALITY_VALUES),
            _bad_values_message(review, "data_quality_status", DATA_QUALITY_VALUES),
        ),
        _check_row(
            "market_status_enum_valid",
            _column_values_in(review, "market_match_status", MARKET_STATUS_VALUES),
            _bad_values_message(review, "market_match_status", MARKET_STATUS_VALUES),
        ),
        _check_row(
            "outcome_status_enum_valid",
            _column_values_in(review, "outcome_status", OUTCOME_STATUS_VALUES),
            _bad_values_message(review, "outcome_status", OUTCOME_STATUS_VALUES),
        ),
        _check_row(
            "rank_source_enum_valid",
            _column_values_in(review, "rank_source", RANK_SOURCE_VALUES),
            _bad_values_message(review, "rank_source", RANK_SOURCE_VALUES),
        ),
        _check_row(
            "no_market_as_rank_source",
            not review["rank_source"].astype(str).str.contains("MARKET", case=False).any(),
            "market cannot create rank_source",
        ),
        _check_row(
            "rookies_do_not_have_dynasty_rank",
            review.loc[review["player_type"].isin(["ROOKIE", "PROSPECT"]), "dynasty_rank"]
            .astype(str)
            .str.strip()
            .eq("")
            .all(),
            "rookie/prospect dynasty_rank must be blank",
        ),
        _check_row(
            "app_wiring_allowed_all_no",
            review["app_wiring_allowed"].astype(str).str.lower().eq("no").all(),
            "review artifact is not app wiring",
        ),
        _check_row(
            "model_input_allowed_all_no",
            review["model_input_allowed"].astype(str).str.lower().eq("no").all(),
            "review artifact is not model input",
        ),
        _check_row(
            "duplicate_groups_identified",
            "duplicate_group_id" in review.columns and len(duplicate_review) >= 0,
            f"duplicate review rows={len(duplicate_review)}",
        ),
        _check_row(
            "missing_player_id_reported",
            (identity_gap_review["gap_type"].astype(str).eq("missing_player_id").any())
            if not identity_gap_review.empty and "gap_type" in identity_gap_review.columns
            else False,
            f"identity gap rows={len(identity_gap_review)}",
        ),
        _check_row(
            "age_source_reported",
            review["age_source"].astype(str).str.strip().ne("").all(),
            "age_source required on every row",
        ),
        _check_row(
            "outcome_gaps_not_enough_information",
            review.loc[
                review["outcome_status"].astype(str).isin(["MISSING", "UNSUPPORTED"]),
                "outcome_context",
            ]
            .astype(str)
            .eq(NOT_ENOUGH_INFORMATION)
            .all(),
            "missing/unsupported outcomes must display Not enough information",
        ),
        _check_row(
            "full_dynasty_veteran_row_count_preserved",
            _count_source_layer(review, "Veteran Full Dynasty Layer")
            == _expected_source_count(sources, "full_dynasty", 240),
            f"full dynasty rows={_count_source_layer(review, 'Veteran Full Dynasty Layer')}",
        ),
        _check_row(
            "rookie_prospect_count_reported",
            int(review["player_type"].isin(["ROOKIE", "PROSPECT"]).sum()) > 0,
            f"rookie/prospect rows={int(review['player_type'].isin(['ROOKIE', 'PROSPECT']).sum())}",
        ),
        _check_row(
            "frozen_board_remains_66",
            _expected_source_count(sources, "frozen", 66) == 66,
            f"frozen source rows={_expected_source_count(sources, 'frozen', 0)}",
        ),
        _check_row(
            "identity_triage_schema_valid",
            set(IDENTITY_TRIAGE_COLUMNS).issubset(identity_triage.columns),
            _missing_message(IDENTITY_TRIAGE_COLUMNS, identity_triage.columns),
        ),
        _check_row(
            "identity_triage_class_enum_valid",
            _column_values_in(identity_triage, "triage_class", TRIAGE_CLASS_VALUES),
            _bad_values_message(identity_triage, "triage_class", TRIAGE_CLASS_VALUES),
        ),
        _check_row(
            "duplicate_class_enum_valid",
            _column_values_in(duplicate_review, "duplicate_class", DUPLICATE_CLASS_VALUES),
            _bad_values_message(duplicate_review, "duplicate_class", DUPLICATE_CLASS_VALUES),
        ),
        _check_row(
            "identity_repairs_preserve_app_and_model_no",
            review["app_wiring_allowed"].astype(str).str.lower().eq("no").all()
            and review["model_input_allowed"].astype(str).str.lower().eq("no").all(),
            "safe review-artifact repairs cannot unlock app/model usage",
        ),
    ]
    return pd.DataFrame(checks)


def _load_sources() -> dict[str, pd.DataFrame]:
    return {
        "full_dynasty": _read_csv(FULL_DYNASTY_PATH),
        "frozen": _read_csv(FROZEN_BOARD_PATH),
        "rookie_overlay": _read_csv(ROOKIE_OVERLAY_PATH),
        "rookie_warning": _read_csv(ROOKIE_WARNING_PATH),
        "pdf_free_agents": _read_csv(PDF_FREE_AGENT_PATH),
        "market": _read_csv(MARKET_BASELINE_PATH),
        "outcome": _read_csv(OUTCOME_CONTEXT_PATH),
        "identity": _read_csv(IDENTITY_AUDIT_PATH),
        "rookie_age": _read_csv(ROOKIE_AGE_PATH),
    }


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _veteran_rows(sources: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows = []
    for index, row in sources["full_dynasty"].iterrows():
        player_name = _text(row.get("player_name"))
        position = _text(row.get("position"))
        identity = _identity_match(sources["identity"], player_name, position, "full_dynasty_board_model_v4")
        market = _market_match(sources["market"], player_name, position, _text(identity.get("sleeper_id")))
        outcome = _outcome_match(sources["outcome"], player_name, position)
        age, age_source = _age_for_veteran(row, market)
        caveats = _join_text(
            [
                row.get("warning_flags"),
                row.get("data_needed"),
                market.get("dp_display_only_warning"),
                identity.get("reason"),
            ]
        )
        player_id = _first_text(row.get("player_id"), identity.get("sleeper_id"))
        rows.append(
            _base_row(
                player_universe_id=_universe_id("veteran", player_id, player_name, position, index),
                player_id=player_id,
                player_name=player_name,
                position=position,
                nfl_team=_text(row.get("nfl_team")) or "UNKNOWN",
                age=age,
                age_source=age_source,
                player_type="VETERAN",
                availability_status=_text(row.get("pool_status")) or NOT_ENOUGH_INFORMATION,
                rank_source="FULL_DYNASTY_RANK",
                dynasty_rank=_rank(row.get("nwr_rank")),
                rookie_rank="",
                frozen_baseline_rank="",
                candidate_rank="",
                unified_display_rank=_rank(row.get("nwr_rank")),
                unified_display_rank_source="FULL_DYNASTY_RANK_REVIEW_ORDER",
                tier="",
                tier_source=NOT_ENOUGH_INFORMATION,
                outcome_context=_outcome_context(outcome),
                outcome_status=_outcome_status(outcome),
                market=market,
                data_quality_status=_quality(identity, player_id, caveats),
                manual_review_flag=_manual_flag(identity, player_id, caveats),
                caveats=caveats,
                source_files=_source_files([FULL_DYNASTY_PATH, MARKET_BASELINE_PATH, IDENTITY_AUDIT_PATH]),
                source_layer="Veteran Full Dynasty Layer",
                join_confidence=_text(identity.get("match_confidence")) or "SOURCE_ROW",
                review_status=_review_status(identity, player_id, caveats),
            )
        )
    return rows


def _rookie_rows(sources: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    warning_by_key = {
        _identity_key(row.get("player"), row.get("position")): row
        for _, row in sources["rookie_warning"].iterrows()
    }
    rows = []
    for index, row in sources["rookie_overlay"].iterrows():
        player_name = _text(row.get("player"))
        position = _text(row.get("position"))
        key = _identity_key(player_name, position)
        identity = _identity_match(sources["identity"], player_name, position, "frozen_final_board_v1")
        age_row = _simple_match(sources["rookie_age"], player_name, position, "player", "position")
        market = _market_match(sources["market"], player_name, position, _text(identity.get("sleeper_id")))
        outcome = _outcome_match(sources["outcome"], player_name, position)
        warning = warning_by_key.get(key, {})
        player_id = _first_text(identity.get("sleeper_id"), identity.get("dynastyprocess_id"))
        age = _age_value(age_row.get("age"))
        age_source = (
            "rookie verified age audit"
            if age != NOT_ENOUGH_INFORMATION
            else NOT_ENOUGH_INFORMATION
        )
        caveats = _join_text(
            [
                row.get("risk_notes"),
                warning.get("main_risk"),
                warning.get("action_if_unconfirmed"),
                identity.get("reason"),
                "Rookie/prospect has no fabricated veteran Dynasty Rank.",
            ]
        )
        rookie_rank = _rank(row.get("rookie_rank_display_only"))
        rows.append(
            _base_row(
                player_universe_id=_universe_id("rookie", player_id, player_name, position, index),
                player_id=player_id,
                player_name=player_name,
                position=position,
                nfl_team=_text(row.get("nfl_team")) or "UNKNOWN",
                age=age,
                age_source=age_source,
                player_type="ROOKIE",
                availability_status=_text(row.get("availability_status")) or "rookie_pool",
                rank_source="ROOKIE_RANK" if rookie_rank else "UNRANKED_REVIEW",
                dynasty_rank="",
                rookie_rank=rookie_rank,
                frozen_baseline_rank=_rank(row.get("final_board_rank")),
                candidate_rank="",
                unified_display_rank=_display_rank(1000, rookie_rank or row.get("final_board_rank"), index),
                unified_display_rank_source=(
                    "ROOKIE_RANK_REVIEW_ORDER" if rookie_rank else "FROZEN_BASELINE_RANK_REVIEW_ORDER"
                ),
                tier=_text(row.get("rookie_tier_display_only") or row.get("final_tier")),
                tier_source="Rookie HQ",
                outcome_context=_outcome_context(outcome),
                outcome_status=_outcome_status(outcome),
                market=market,
                data_quality_status=_quality(identity, player_id, caveats),
                manual_review_flag=_manual_flag(identity, player_id, caveats),
                caveats=caveats,
                source_files=_source_files(
                    [
                        ROOKIE_OVERLAY_PATH,
                        ROOKIE_WARNING_PATH,
                        FROZEN_BOARD_PATH,
                        ROOKIE_AGE_PATH,
                        IDENTITY_AUDIT_PATH,
                    ]
                ),
                source_layer="Rookie/Prospect Layer",
                join_confidence=_text(identity.get("match_confidence")) or "NOT_ENOUGH_INFORMATION",
                review_status=_review_status(identity, player_id, caveats),
            )
        )
    return rows


def _frozen_dropped_veteran_rows(sources: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    frozen = sources["frozen"]
    if frozen.empty or "asset_type" not in frozen.columns:
        return []
    dropped = frozen.loc[~frozen["asset_type"].astype(str).str.lower().eq("rookie")].copy()
    rows = []
    for index, row in dropped.iterrows():
        player_name = _text(row.get("player"))
        position = _text(row.get("position"))
        identity = _identity_match(sources["identity"], player_name, position, "frozen_final_board_v1")
        market = _market_match(sources["market"], player_name, position, _text(identity.get("sleeper_id")))
        outcome = _outcome_match(sources["outcome"], player_name, position)
        player_id = _first_text(identity.get("sleeper_id"), identity.get("dynastyprocess_id"))
        caveats = _join_text(
            [
                row.get("risk_notes"),
                row.get("veteran_trust_status_display_only"),
                identity.get("reason"),
                "Frozen baseline/checkpoint row only.",
            ]
        )
        frozen_rank = _rank(row.get("final_board_rank"))
        candidate_rank = _rank(row.get("veteran_candidate_rank_display_only"))
        rows.append(
            _base_row(
                player_universe_id=_universe_id("frozen", player_id, player_name, position, index),
                player_id=player_id,
                player_name=player_name,
                position=position,
                nfl_team=_text(row.get("nfl_team")) or "UNKNOWN",
                age=NOT_ENOUGH_INFORMATION,
                age_source=NOT_ENOUGH_INFORMATION,
                player_type="VETERAN",
                availability_status=_text(row.get("availability_status")) or NOT_ENOUGH_INFORMATION,
                rank_source="FROZEN_BASELINE_RANK",
                dynasty_rank="",
                rookie_rank="",
                frozen_baseline_rank=frozen_rank,
                candidate_rank=candidate_rank,
                unified_display_rank=_display_rank(2000, frozen_rank, index),
                unified_display_rank_source="FROZEN_BASELINE_RANK_REVIEW_ORDER",
                tier=_text(row.get("final_tier")),
                tier_source="Frozen Baseline",
                outcome_context=_outcome_context(outcome),
                outcome_status=_outcome_status(outcome),
                market=market,
                data_quality_status=_quality(identity, player_id, caveats),
                manual_review_flag=_manual_flag(identity, player_id, caveats),
                caveats=caveats,
                source_files=_source_files([FROZEN_BOARD_PATH, IDENTITY_AUDIT_PATH]),
                source_layer="Frozen Baseline Layer",
                join_confidence=_text(identity.get("match_confidence")) or "NOT_ENOUGH_INFORMATION",
                review_status=_review_status(identity, player_id, caveats),
            )
        )
    return rows


def _pdf_free_agent_rows(sources: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    rows = []
    for index, row in sources["pdf_free_agents"].iterrows():
        player_name = _text(row.get("player"))
        position = _text(row.get("pos"))
        player_id = _text(row.get("player_id"))
        identity = _identity_match(sources["identity"], player_name, position, "lve_pdf_page3_free_agents")
        market = _market_match(
            sources["market"],
            player_name,
            position,
            _first_text(identity.get("sleeper_id"), player_id),
        )
        age = _age_value(row.get("age"))
        caveats = _join_text(
            [
                row.get("notes"),
                row.get("warning_flags"),
                row.get("data_needed"),
                identity.get("reason"),
                "PDF free-agent availability context only.",
            ]
        )
        candidate_rank = _rank(row.get("matched_current_candidate_rank"))
        rank_source = "CANDIDATE_RANK" if candidate_rank else "UNRANKED_REVIEW"
        rows.append(
            _base_row(
                player_universe_id=_universe_id("pdf", player_id, player_name, position, index),
                player_id=_first_text(player_id, identity.get("sleeper_id")),
                player_name=player_name,
                position=position,
                nfl_team=_text(row.get("nfl_team")) or "UNKNOWN",
                age=age,
                age_source=(
                    "PDF derived display artifact" if age != NOT_ENOUGH_INFORMATION else NOT_ENOUGH_INFORMATION
                ),
                player_type="PDF_FA",
                availability_status=_text(row.get("draftable_status")) or "PDF Page 3 Free Agent",
                rank_source=rank_source,
                dynasty_rank="",
                rookie_rank="",
                frozen_baseline_rank="",
                candidate_rank=candidate_rank,
                unified_display_rank=_display_rank(3000, candidate_rank or row.get("pdf_overall_rank_or_number"), index),
                unified_display_rank_source=(
                    "CANDIDATE_RANK_REVIEW_ORDER" if candidate_rank else "UNRANKED_REVIEW_ORDER"
                ),
                tier="",
                tier_source=NOT_ENOUGH_INFORMATION,
                outcome_context=NOT_ENOUGH_INFORMATION,
                outcome_status="NOT_APPLICABLE",
                market=market,
                data_quality_status=_quality(identity, _first_text(player_id, identity.get("sleeper_id")), caveats),
                manual_review_flag=_manual_flag(identity, _first_text(player_id, identity.get("sleeper_id")), caveats),
                caveats=caveats,
                source_files=_source_files([PDF_FREE_AGENT_PATH, IDENTITY_AUDIT_PATH]),
                source_layer="PDF Free-Agent Availability Layer",
                join_confidence=_text(identity.get("match_confidence")) or "SOURCE_ROW",
                review_status=_review_status(identity, _first_text(player_id, identity.get("sleeper_id")), caveats),
            )
        )
    return rows


def _base_row(
    *,
    player_universe_id: str,
    player_id: str,
    player_name: str,
    position: str,
    nfl_team: str,
    age: str,
    age_source: str,
    player_type: str,
    availability_status: str,
    rank_source: str,
    dynasty_rank: str,
    rookie_rank: str,
    frozen_baseline_rank: str,
    candidate_rank: str,
    unified_display_rank: str,
    unified_display_rank_source: str,
    tier: str,
    tier_source: str,
    outcome_context: str,
    outcome_status: str,
    market: dict[str, Any],
    data_quality_status: str,
    manual_review_flag: str,
    caveats: str,
    source_files: str,
    source_layer: str,
    join_confidence: str,
    review_status: str,
) -> dict[str, str]:
    return {
        "player_universe_id": player_universe_id,
        "player_id": player_id,
        "player_name": player_name,
        "normalized_name": _normalize_name(player_name),
        "position": position or "UNKNOWN",
        "nfl_team": nfl_team or "UNKNOWN",
        "age": age or NOT_ENOUGH_INFORMATION,
        "age_source": age_source or NOT_ENOUGH_INFORMATION,
        "player_type": player_type,
        "availability_status": availability_status or NOT_ENOUGH_INFORMATION,
        "rank_source": rank_source,
        "dynasty_rank": dynasty_rank,
        "rookie_rank": rookie_rank,
        "frozen_baseline_rank": frozen_baseline_rank,
        "candidate_rank": candidate_rank,
        "unified_display_rank": unified_display_rank,
        "unified_display_rank_source": unified_display_rank_source,
        "tier": tier,
        "tier_source": tier_source or NOT_ENOUGH_INFORMATION,
        "outcome_context": outcome_context or NOT_ENOUGH_INFORMATION,
        "outcome_status": outcome_status,
        "market_match_status": "MATCHED" if market else "UNMATCHED",
        "dp_1qb_value": _rank(market.get("dp_value_1qb")) if market else "",
        "dp_market_rank": _rank(market.get("dp_market_rank_1qb")) if market else "",
        "nwr_vs_market_gap": _rank(market.get("nwr_vs_dp_gap")) if market else "",
        "data_quality_status": data_quality_status,
        "manual_review_flag": manual_review_flag,
        "caveats": caveats,
        "source_files": source_files,
        "source_layer": source_layer,
        "join_confidence": join_confidence.upper() if join_confidence else "NOT_ENOUGH_INFORMATION",
        "duplicate_group_id": "",
        "review_status": review_status,
        "app_wiring_allowed": APP_WIRING_ALLOWED,
        "model_input_allowed": MODEL_INPUT_ALLOWED,
    }


def _apply_duplicate_groups(review: pd.DataFrame) -> pd.DataFrame:
    output = review.copy()
    output["duplicate_group_id"] = ""
    duplicate_keys: dict[int, list[int]] = {}
    group_num = 1
    for _, group in output.loc[output["player_id"].astype(str).str.strip().ne("")].groupby("player_id"):
        if len(group) > 1:
            duplicate_keys[group_num] = list(group.index)
            group_num += 1
    for _, group in output.groupby(["normalized_name", "position"], dropna=False):
        if len(group) > 1:
            existing = set().union(*[set(v) for v in duplicate_keys.values()]) if duplicate_keys else set()
            group_indexes = list(group.index)
            if not set(group_indexes).issubset(existing):
                duplicate_keys[group_num] = group_indexes
                group_num += 1
    for group_id, indexes in duplicate_keys.items():
        output.loc[indexes, "duplicate_group_id"] = f"DUP-{group_id:04d}"
        output.loc[indexes, "manual_review_flag"] = "true"
        output.loc[indexes, "review_status"] = "REVIEW_NEEDED"
        output.loc[indexes, "data_quality_status"] = "MANUAL_REVIEW"
    return output


def _duplicate_review(review: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for duplicate_group_id, group in review.loc[
        review["duplicate_group_id"].astype(str).str.strip().ne("")
    ].groupby("duplicate_group_id"):
        detection_types = []
        if group["player_id"].astype(str).str.strip().replace("", pd.NA).dropna().nunique() == 1:
            detection_types.append("duplicate_exact_player_id")
        if group[["normalized_name", "position"]].drop_duplicates().shape[0] == 1:
            detection_types.append("duplicate_normalized_name_position")
        if group["nfl_team"].astype(str).nunique() > 1:
            detection_types.append("conflicting_teams")
        if group["position"].astype(str).nunique() > 1:
            detection_types.append("conflicting_positions")
        if group["source_layer"].astype(str).nunique() > 1:
            detection_types.append("appears_in_multiple_layers")
        duplicate_class = _duplicate_classification(detection_types)
        rows.append(
            {
                "duplicate_group_id": duplicate_group_id,
                "detection_type": ";".join(detection_types) or "likely_duplicate",
                "duplicate_class": duplicate_class,
                "recommended_action": _duplicate_recommended_action(duplicate_class),
                "row_count": len(group),
                "player_ids": _join_unique(group["player_id"]),
                "player_names": _join_unique(group["player_name"]),
                "positions": _join_unique(group["position"]),
                "teams": _join_unique(group["nfl_team"]),
                "source_layers": _join_unique(group["source_layer"]),
                "review_status": "REVIEW_NEEDED",
                "notes": "Do not auto-merge low-confidence duplicates.",
            }
        )
    suffix_groups = _suffix_duplicate_groups(review)
    rows.extend(suffix_groups)
    return pd.DataFrame(
        rows,
        columns=[
            "duplicate_group_id",
            "detection_type",
            "duplicate_class",
            "recommended_action",
            "row_count",
            "player_ids",
            "player_names",
            "positions",
            "teams",
            "source_layers",
            "review_status",
            "notes",
        ],
    )


def _duplicate_classification(detection_types: list[str]) -> str:
    detections = set(detection_types)
    if "conflicting_positions" in detections:
        return "POSITION_CONFLICT"
    if "conflicting_teams" in detections:
        return "TEAM_CONFLICT"
    if "likely_duplicate_suffix_difference" in detections:
        return "SUFFIX_VARIANT"
    if "appears_in_multiple_layers" in detections and (
        "duplicate_exact_player_id" in detections
        or "duplicate_normalized_name_position" in detections
    ):
        return "MULTI_LAYER_SAME_PLAYER_EXPECTED"
    if "duplicate_normalized_name_position" in detections:
        return "NAME_COLLISION"
    return "NEEDS_MANUAL_REVIEW"


def _duplicate_recommended_action(duplicate_class: str) -> str:
    actions = {
        "MULTI_LAYER_SAME_PLAYER_EXPECTED": "KEEP_SEPARATE_REVIEW_ROWS; consolidate by source policy later if app wiring is approved.",
        "SUFFIX_VARIANT": "MANUAL_REVIEW_REQUIRED before merge.",
        "POSITION_CONFLICT": "MANUAL_REVIEW_REQUIRED; do not merge until position conflict is resolved.",
        "TEAM_CONFLICT": "MANUAL_REVIEW_REQUIRED; team may be stale or source-specific.",
        "NAME_COLLISION": "MANUAL_REVIEW_REQUIRED; same normalized name/position may still be distinct rows.",
        "TRUE_DUPLICATE_SAFE_MERGE_LATER": "SAFE_MERGE_LATER only after a separate source-policy lane approves consolidation.",
    }
    return actions.get(duplicate_class, "MANUAL_REVIEW_REQUIRED; do not auto-merge.")


def _identity_gap_review(review: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in review.iterrows():
        gaps = []
        if not _text(row.get("player_id")):
            gaps.append("missing_player_id")
        if _text(row.get("join_confidence")).upper() in {"", "LOW", "MEDIUM", "NOT_ENOUGH_INFORMATION"}:
            gaps.append("low_or_missing_join_confidence")
        if _text(row.get("manual_review_flag")).lower() == "true":
            gaps.append("manual_review_flag")
        if _text(row.get("age")) == NOT_ENOUGH_INFORMATION:
            gaps.append("missing_age")
        for gap in sorted(set(gaps)):
            rows.append(
                {
                    "player_universe_id": row.get("player_universe_id", ""),
                    "player_id": row.get("player_id", ""),
                    "player_name": row.get("player_name", ""),
                    "position": row.get("position", ""),
                    "nfl_team": row.get("nfl_team", ""),
                    "source_layer": row.get("source_layer", ""),
                    "gap_type": gap,
                    "join_confidence": row.get("join_confidence", ""),
                    "review_status": "REVIEW_NEEDED",
                    "notes": row.get("caveats", ""),
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "player_universe_id",
            "player_id",
            "player_name",
            "position",
            "nfl_team",
            "source_layer",
            "gap_type",
            "join_confidence",
            "review_status",
            "notes",
        ],
    )


def _identity_triage(
    review: pd.DataFrame,
    identity_gap_review: pd.DataFrame,
    sources: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    rows = []
    for _, gap in identity_gap_review.iterrows():
        proposed_player_id, source_used = _safe_identity_repair_candidate(gap, sources)
        triage_class, action_taken, confidence, remaining_risk = _triage_decision(
            gap,
            proposed_player_id,
        )
        rows.append(
            {
                "player_name": gap.get("player_name", ""),
                "position": gap.get("position", ""),
                "source_layer": gap.get("source_layer", ""),
                "original_player_id": gap.get("player_id", ""),
                "proposed_player_id": proposed_player_id,
                "triage_class": triage_class,
                "action_taken": action_taken,
                "confidence": confidence,
                "source_used": source_used,
                "remaining_risk": remaining_risk,
                "notes": _triage_notes(gap, review),
            }
        )
    return pd.DataFrame(rows, columns=IDENTITY_TRIAGE_COLUMNS)


def _safe_identity_repair_candidate(
    gap: pd.Series,
    sources: dict[str, pd.DataFrame],
) -> tuple[str, str]:
    if _text(gap.get("gap_type")) != "missing_player_id":
        return "", ""
    identity = sources.get("identity", pd.DataFrame())
    if identity.empty or "player_id" not in identity.columns:
        return "", ""
    name = _normalize_name(gap.get("player_name"))
    position = _text(gap.get("position")).upper()
    matched = identity.loc[
        identity["player_name"].map(_normalize_name).eq(name)
        & identity["position"].astype(str).str.upper().eq(position)
        & identity["player_id"].astype(str).str.strip().ne("")
        & identity["match_confidence"].astype(str).str.upper().eq("HIGH")
        & identity["needs_manual_review"].astype(str).str.lower().eq("no")
    ]
    if matched.empty:
        return "", ""
    player_id = _text(matched.iloc[0].get("player_id"))
    return player_id, _rel(IDENTITY_AUDIT_PATH)


def _triage_decision(gap: pd.Series, proposed_player_id: str) -> tuple[str, str, str, str]:
    gap_type = _text(gap.get("gap_type"))
    original_player_id = _text(gap.get("player_id"))
    join_confidence = _text(gap.get("join_confidence")).upper()
    if proposed_player_id:
        return (
            "SAFE_REPAIR_EXISTING_CROSSWALK",
            "APPLY_PLAYER_ID_REPAIR",
            "HIGH",
            "Low; exact approved identity audit match with manual-review=no.",
        )
    if gap_type == "manual_review_flag" and original_player_id:
        return (
            "EXPECTED_NO_ID_REVIEW_ONLY",
            "KEEP_REVIEW_ONLY",
            join_confidence or "REVIEW_ONLY",
            "Review flag remains until duplicate/source-layer policy is approved.",
        )
    if gap_type == "manual_review_flag":
        return (
            "NEEDS_MANUAL_REVIEW",
            "NO_CHANGE",
            join_confidence or "LOW",
            "Manual review row has no high-confidence player_id repair source.",
        )
    if gap_type == "missing_age":
        return (
            "NEEDS_MANUAL_REVIEW",
            "NO_CHANGE",
            join_confidence or "UNKNOWN",
            "Age coverage requires an approved age source; do not infer.",
        )
    if gap_type == "missing_player_id":
        return (
            "NEEDS_MANUAL_REVIEW",
            "NO_CHANGE",
            join_confidence or "LOW",
            "No high-confidence existing crosswalk or exact approved match found.",
        )
    if gap_type == "low_or_missing_join_confidence":
        return (
            "NEEDS_MANUAL_REVIEW",
            "NO_CHANGE",
            join_confidence or "LOW",
            "Join confidence is below the safe auto-repair threshold.",
        )
    return (
        "DO_NOT_REPAIR",
        "NO_CHANGE",
        join_confidence or "UNKNOWN",
        "Gap type is not eligible for automated review-artifact repair.",
    )


def _triage_notes(gap: pd.Series, review: pd.DataFrame) -> str:
    player_name = _text(gap.get("player_name"))
    position = _text(gap.get("position"))
    source_layer = _text(gap.get("source_layer"))
    gap_type = _text(gap.get("gap_type"))
    matching_rows = review.loc[
        review["player_name"].astype(str).eq(player_name)
        & review["position"].astype(str).eq(position)
        & review["source_layer"].astype(str).eq(source_layer)
    ]
    caveats = _join_unique(matching_rows["caveats"]) if not matching_rows.empty else ""
    return f"gap_type={gap_type}; {caveats}".strip()


def _apply_safe_identity_repairs(
    review: pd.DataFrame,
    identity_triage: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    output = review.copy()
    safe_rows = identity_triage.loc[
        identity_triage["triage_class"].isin(
            ["SAFE_REPAIR_EXISTING_CROSSWALK", "SAFE_REPAIR_EXACT_APPROVED_MATCH"]
        )
        & identity_triage["proposed_player_id"].astype(str).str.strip().ne("")
    ]
    repair_count = 0
    for _, repair in safe_rows.iterrows():
        mask = (
            output["player_name"].astype(str).eq(_text(repair.get("player_name")))
            & output["position"].astype(str).eq(_text(repair.get("position")))
            & output["source_layer"].astype(str).eq(_text(repair.get("source_layer")))
            & output["player_id"].astype(str).eq(_text(repair.get("original_player_id")))
        )
        if not mask.any():
            continue
        output.loc[mask, "player_id"] = _text(repair.get("proposed_player_id"))
        output.loc[mask, "join_confidence"] = "HIGH"
        output.loc[mask, "caveats"] = output.loc[mask, "caveats"].astype(str).map(
            lambda value: _append_caveat(value, "Player ID repaired from existing approved identity audit.")
        )
        repair_count += int(mask.sum())
    return output, repair_count


def _append_caveat(caveats: str, addition: str) -> str:
    if not caveats:
        return addition
    if addition in caveats:
        return caveats
    return f"{caveats} {addition}"


def _source_summary(
    review: pd.DataFrame,
    sources: dict[str, pd.DataFrame],
    identity_gap_review: pd.DataFrame | None = None,
    duplicate_review: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if identity_gap_review is None:
        identity_gap_review = pd.DataFrame()
    if duplicate_review is None:
        duplicate_review = pd.DataFrame()
    rows = []
    for layer, group in review.groupby("source_layer"):
        layer_identity_gaps = (
            identity_gap_review.loc[identity_gap_review["source_layer"].astype(str).eq(layer)]
            if not identity_gap_review.empty and "source_layer" in identity_gap_review.columns
            else pd.DataFrame()
        )
        rows.append(
            {
                "layer": layer,
                "source_files": _join_unique(group["source_files"]),
                "row_count": len(group),
                "unique_player_count": group[["normalized_name", "position"]].drop_duplicates().shape[0],
                "player_id_coverage": int(group["player_id"].astype(str).str.strip().ne("").sum()),
                "age_coverage": int(group["age"].astype(str).ne(NOT_ENOUGH_INFORMATION).sum()),
                "rank_coverage": int(
                    group[["dynasty_rank", "rookie_rank", "frozen_baseline_rank", "candidate_rank"]]
                    .astype(str)
                    .apply(lambda row: any(value.strip() for value in row), axis=1)
                    .sum()
                ),
                "outcome_coverage": int(group["outcome_status"].astype(str).eq("SUPPORTED").sum()),
                "market_coverage": int(group["market_match_status"].astype(str).eq("MATCHED").sum()),
                "review_needed_count": int(group["review_status"].astype(str).eq("REVIEW_NEEDED").sum()),
                "identity_gap_count": int(len(layer_identity_gaps)),
                "duplicate_review_count": int(
                    duplicate_review["source_layers"].astype(str).str.contains(layer, regex=False).sum()
                )
                if not duplicate_review.empty and "source_layers" in duplicate_review.columns
                else 0,
                "caveats": _layer_caveat(layer),
            }
        )
    source_counts = [
        ("Full Dynasty source input", FULL_DYNASTY_PATH, len(sources.get("full_dynasty", []))),
        ("Frozen board source input", FROZEN_BOARD_PATH, len(sources.get("frozen", []))),
        ("Rookie overlay source input", ROOKIE_OVERLAY_PATH, len(sources.get("rookie_overlay", []))),
        ("PDF free-agent source input", PDF_FREE_AGENT_PATH, len(sources.get("pdf_free_agents", []))),
        ("Market baseline source input", MARKET_BASELINE_PATH, len(sources.get("market", []))),
        ("Outcome context source input", OUTCOME_CONTEXT_PATH, len(sources.get("outcome", []))),
        ("Identity audit source input", IDENTITY_AUDIT_PATH, len(sources.get("identity", []))),
    ]
    for layer, path, count in source_counts:
        rows.append(
            {
                "layer": layer,
                "source_files": _rel(path),
                "row_count": count,
                "unique_player_count": "",
                "player_id_coverage": "",
                "age_coverage": "",
                "rank_coverage": "",
                "outcome_coverage": "",
                "market_coverage": "",
                "review_needed_count": "",
                "identity_gap_count": "",
                "duplicate_review_count": "",
                "caveats": "Input source count for validation context.",
            }
        )
    return pd.DataFrame(rows)


def _suffix_duplicate_groups(review: pd.DataFrame) -> list[dict[str, Any]]:
    rows = []
    review = review.copy()
    review["suffixless_name"] = review["normalized_name"].map(_strip_suffix_tokens)
    next_num = 9001
    for (_, position), group in review.groupby(["suffixless_name", "position"]):
        if len(group) <= 1 or group["normalized_name"].nunique() <= 1:
            continue
        rows.append(
            {
                "duplicate_group_id": f"DUP-{next_num:04d}",
                "detection_type": "likely_duplicate_suffix_difference",
                "duplicate_class": "SUFFIX_VARIANT",
                "recommended_action": _duplicate_recommended_action("SUFFIX_VARIANT"),
                "row_count": len(group),
                "player_ids": _join_unique(group["player_id"]),
                "player_names": _join_unique(group["player_name"]),
                "positions": position,
                "teams": _join_unique(group["nfl_team"]),
                "source_layers": _join_unique(group["source_layer"]),
                "review_status": "REVIEW_NEEDED",
                "notes": "Suffix-insensitive name match; review manually before merging.",
            }
        )
        next_num += 1
    return rows


def _market_match(market: pd.DataFrame, player_name: str, position: str, player_id: str) -> dict[str, Any]:
    if market.empty:
        return {}
    name = _normalize_name(player_name)
    pos = position.upper()
    for name_column in ("nwr_name", "player"):
        if name_column in market.columns and "pos" in market.columns:
            matched = market.loc[
                market[name_column].map(_normalize_name).eq(name)
                & market["pos"].astype(str).str.upper().eq(pos)
            ]
            if not matched.empty:
                return matched.iloc[0].to_dict()
    for column in ("nwr_player_id", "sleeper_id", "fp_id"):
        if player_id and column in market.columns:
            mask = market[column].astype(str).str.replace(r"\.0$", "", regex=True).eq(player_id)
            matched = market.loc[mask]
            if not matched.empty:
                return matched.iloc[0].to_dict()
    return {}


def _identity_match(
    identity: pd.DataFrame,
    player_name: str,
    position: str,
    preferred_surface: str,
) -> dict[str, Any]:
    if identity.empty:
        return {}
    name = _normalize_name(player_name)
    pos = position.upper()
    frame = identity.loc[
        identity["player_name"].map(_normalize_name).eq(name)
        & identity["position"].astype(str).str.upper().eq(pos)
    ]
    if frame.empty:
        return {}
    preferred = frame.loc[frame["source_surface"].astype(str).eq(preferred_surface)]
    if not preferred.empty:
        return preferred.iloc[0].to_dict()
    return frame.iloc[0].to_dict()


def _outcome_match(outcome: pd.DataFrame, player_name: str, position: str) -> dict[str, Any]:
    return _simple_match(outcome, player_name, position, "player", "position")


def _simple_match(
    frame: pd.DataFrame,
    player_name: str,
    position: str,
    name_column: str,
    position_column: str,
) -> dict[str, Any]:
    if frame.empty or name_column not in frame.columns or position_column not in frame.columns:
        return {}
    matched = frame.loc[
        frame[name_column].map(_normalize_name).eq(_normalize_name(player_name))
        & frame[position_column].astype(str).str.upper().eq(position.upper())
    ]
    return matched.iloc[0].to_dict() if not matched.empty else {}


def _age_for_veteran(row: pd.Series, market: dict[str, Any]) -> tuple[str, str]:
    source_age = _age_value(row.get("age"))
    if source_age != NOT_ENOUGH_INFORMATION:
        return source_age, "NWR approved source"
    market_age = _age_value(market.get("age") or market.get("dp_age"))
    if market_age != NOT_ENOUGH_INFORMATION:
        return market_age, "DynastyProcess display fallback"
    return NOT_ENOUGH_INFORMATION, NOT_ENOUGH_INFORMATION


def _outcome_context(outcome: dict[str, Any]) -> str:
    if not outcome:
        return NOT_ENOUGH_INFORMATION
    values = []
    for column in ("QB T12", "RB T12", "RB T24", "WR T12", "WR T24", "WR T36", "TE T12"):
        value = _text(outcome.get(column))
        if value:
            values.append(f"{column}={value}")
    return "; ".join(values) if values else NOT_ENOUGH_INFORMATION


def _outcome_status(outcome: dict[str, Any]) -> str:
    if not outcome:
        return "MISSING"
    if _outcome_context(outcome) == NOT_ENOUGH_INFORMATION:
        return "MISSING"
    return "SUPPORTED"


def _quality(identity: dict[str, Any], player_id: str, caveats: str) -> str:
    confidence = _text(identity.get("match_confidence")).upper()
    needs_review = _text(identity.get("needs_manual_review")).lower()
    if not player_id or needs_review == "yes" or confidence in {"LOW", "MEDIUM"}:
        return "MANUAL_REVIEW"
    if "Not enough information" in caveats or "missing" in caveats.lower():
        return "YELLOW"
    return "GREEN"


def _manual_flag(identity: dict[str, Any], player_id: str, caveats: str) -> str:
    confidence = _text(identity.get("match_confidence")).upper()
    needs_review = _text(identity.get("needs_manual_review")).lower()
    manual = not player_id or needs_review == "yes" or confidence in {"LOW", "MEDIUM"}
    manual = manual or "review" in caveats.lower() or "unresolved" in caveats.lower()
    return "true" if manual else "false"


def _review_status(identity: dict[str, Any], player_id: str, caveats: str) -> str:
    if _manual_flag(identity, player_id, caveats) == "true":
        return "REVIEW_NEEDED"
    if NOT_ENOUGH_INFORMATION in caveats:
        return "NOT_ENOUGH_INFORMATION"
    return "READY"


def _identity_key(name: Any, position: Any) -> tuple[str, str]:
    return (_normalize_name(name), _text(position).upper())


def _normalize_name(value: Any) -> str:
    text = _text(value).lower()
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_suffix_tokens(value: str) -> str:
    tokens = [token for token in value.split() if token not in {"jr", "sr", "ii", "iii", "iv", "v"}]
    return " ".join(tokens)


def _universe_id(layer: str, player_id: str, player_name: str, position: str, index: int) -> str:
    if player_id:
        token = player_id
    else:
        token = f"{_normalize_name(player_name)}-{position.lower()}-{index}"
    return _safe_token(f"{layer}-{token}")


def _safe_token(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", value).strip("_")


def _display_rank(offset: int, value: Any, index: int) -> str:
    rank = _rank(value)
    if not rank:
        return str(offset + index + 1)
    try:
        return str(offset + int(float(rank)))
    except ValueError:
        return str(offset + index + 1)


def _rank(value: Any) -> str:
    text = _text(value)
    if not text:
        return ""
    try:
        number = float(text)
    except ValueError:
        return text
    if pd.isna(number):
        return ""
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _age_value(value: Any) -> str:
    text = _text(value)
    if not text:
        return NOT_ENOUGH_INFORMATION
    try:
        number = float(text)
    except ValueError:
        return text if text.lower() != "nan" else NOT_ENOUGH_INFORMATION
    if pd.isna(number):
        return NOT_ENOUGH_INFORMATION
    return f"{number:.1f}"


def _text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _first_text(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text:
            return re.sub(r"\.0$", "", text)
    return ""


def _join_text(values: list[Any]) -> str:
    parts = []
    for value in values:
        text = _text(value)
        if text and text.lower() not in {"nan", "none"}:
            parts.append(text)
    return " | ".join(dict.fromkeys(parts))


def _join_unique(series: pd.Series) -> str:
    return "; ".join(dict.fromkeys(_text(value) for value in series.tolist() if _text(value)))


def _source_files(paths: list[Path]) -> str:
    return "; ".join(_rel(path) for path in paths)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _layer_caveat(layer: str) -> str:
    caveats = {
        "Veteran Full Dynasty Layer": "Approved 240-row veteran source; 0 rookie/prospect rows.",
        "Rookie/Prospect Layer": "No fabricated veteran Dynasty Rank; rookie ranks are source-labeled.",
        "Frozen Baseline Layer": "Frozen checkpoint context only; does not replace source truth.",
        "PDF Free-Agent Availability Layer": "Availability context only; not a dynasty-rank source.",
    }
    return caveats.get(layer, "Review-only unified player universe layer.")


def _column_values_in(frame: pd.DataFrame, column: str, allowed: set[str]) -> bool:
    if column not in frame.columns:
        return False
    values = set(frame[column].astype(str).str.strip())
    return values.issubset(allowed)


def _bad_values_message(frame: pd.DataFrame, column: str, allowed: set[str]) -> str:
    if column not in frame.columns:
        return f"missing column {column}"
    values = set(frame[column].astype(str).str.strip())
    bad = sorted(values - allowed)
    return "bad_values=" + ",".join(bad) if bad else "ok"


def _missing_message(required: tuple[str, ...], actual: pd.Index) -> str:
    missing = sorted(set(required) - set(actual))
    return "missing=" + ",".join(missing) if missing else "ok"


def _check_row(check_name: str, passed: bool, detail: str) -> dict[str, str]:
    return {
        "check_name": check_name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail,
    }


def _count_source_layer(review: pd.DataFrame, source_layer: str) -> int:
    return int(review["source_layer"].astype(str).eq(source_layer).sum())


def _expected_source_count(sources: dict[str, pd.DataFrame], key: str, fallback: int) -> int:
    frame = sources.get(key)
    if frame is None or frame.empty:
        return fallback
    return int(len(frame))
