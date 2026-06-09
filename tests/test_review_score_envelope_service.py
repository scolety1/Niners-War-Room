from __future__ import annotations

import pytest

from src.services.review_score_envelope_service import (
    MODEL_V4_CURRENT_PLAYER_CHECKPOINT,
    MODEL_V4_DYNASTY_ASSET,
    ReviewScoreEnvelope,
    UnknownScoreSourceError,
    classify_score_layer,
    envelope_from_row,
    export_score_disclosure,
    market_display_context,
    resolve_primary_score_source,
    row_has_market_display_fields,
    validate_score_envelope,
)


def _envelope(**overrides: object) -> ReviewScoreEnvelope:
    values = {
        "asset_id": "player:keenan-allen",
        "asset_type": "player",
        "display_name": "Keenan Allen",
        "primary_review_score": 41.6097,
        "source_path": (
            "local_exports/model_v4/current_value/latest/"
            "current_player_value_review_rows.csv"
        ),
        "source_column": "checkpoint_review_score",
        "model_version": "model_v4_phase_11g_current_value_checkpoint_0.1.0",
        "lineage_class": "review_v4_current_player",
        "score_type": "checkpoint_review_score",
        "score_as_of_date": "2026-05-30",
        "confidence_cap": 0.8,
        "warnings": ("team_mismatch/source_review",),
        "legacy_formula_warning": False,
        "stale_or_legacy_formula_warning": False,
        "market_display_only": False,
        "manual_decision_required": False,
        "allowed_use": "review_only_current_value_checkpoint",
        "blocked_use": "do_not_use_as_final_recommendation",
        "legacy_active_pack_score": None,
        "market_context": None,
        "display_context": None,
    }
    values.update(overrides)
    return ReviewScoreEnvelope(**values)  # type: ignore[arg-type]


def test_score_envelope_requires_required_source_disclosure_fields() -> None:
    missing_source = _envelope(source_path=None)
    validated = validate_score_envelope(missing_source)

    assert validated.primary_review_score is None
    assert validated.manual_decision_required is True
    assert "missing_score_disclosure_fields" in validated.warnings

    missing_model_version = _envelope(model_version="")
    validated_model_version = validate_score_envelope(missing_model_version)

    assert validated_model_version.primary_review_score is None
    assert validated_model_version.manual_decision_required is True
    assert "missing_score_disclosure_fields" in validated_model_version.warnings


def test_score_envelope_allows_clean_model_v4_current_player_primary_score() -> None:
    validated = validate_score_envelope(_envelope())

    assert validated.primary_review_score == 41.6097
    assert validated.manual_decision_required is False
    assert validated.lineage_class == "review_v4_current_player"


def test_score_envelope_legacy_lineage_is_comparison_only() -> None:
    legacy = _envelope(
        primary_review_score=82.4,
        source_path="local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv",
        source_column="private_score",
        model_version="veteran_lve_stats_first_v1_0_0",
        lineage_class="legacy_active_pack",
        score_type="legacy_active_pack_score",
    )

    validated = validate_score_envelope(legacy)

    assert validated.primary_review_score is None
    assert validated.legacy_active_pack_score == 82.4
    assert validated.legacy_formula_warning is True
    assert validated.stale_or_legacy_formula_warning is True
    assert validated.manual_decision_required is True
    assert "legacy_score_comparison_only" in validated.warnings


def test_score_envelope_unknown_lineage_is_manual_decision_required() -> None:
    unknown = _envelope(lineage_class="unknown")

    validated = validate_score_envelope(unknown)

    assert validated.primary_review_score is None
    assert validated.manual_decision_required is True
    assert "unknown_or_market_only_lineage" in validated.warnings


def test_score_envelope_market_only_cannot_be_primary_score() -> None:
    market_only = _envelope(
        lineage_class="market_display_only",
        market_display_only=True,
        score_type="market_context_score",
    )

    validated = validate_score_envelope(market_only)

    assert validated.primary_review_score is None
    assert validated.manual_decision_required is True
    assert "unknown_or_market_only_lineage" in validated.warnings


def test_score_classifier_identifies_canonical_sources_and_legacy_alias() -> None:
    assert (
        classify_score_layer(
            {
                "source_path": (
                    "local_exports/model_v4/current_value/latest/"
                    "current_player_value_review_rows.csv"
                )
            }
        )
        == "review_v4_current_player"
    )
    assert (
        classify_score_layer(
            {
                "source_path": (
                    "local_exports/model_v4/dynasty_asset_value/latest/"
                    "dynasty_asset_value_review_rows.csv"
                )
            }
        )
        == "review_v4_dynasty_asset"
    )
    assert (
        classify_score_layer({"model_version": "veteran_lve_stats_first_v1_0_0"})
        == "legacy_active_pack"
    )
    assert classify_score_layer({"lineage_class": "legacy"}) == "legacy_active_pack"
    assert classify_score_layer({"market_display_only": True}) == "market_display_only"


def test_score_resolver_declares_player_board_and_cross_asset_primary_sources() -> None:
    assert resolve_primary_score_source("player_board", "player") == (
        MODEL_V4_CURRENT_PLAYER_CHECKPOINT
    )
    assert resolve_primary_score_source("startup_slot_simulator", "player") == (
        MODEL_V4_DYNASTY_ASSET
    )
    assert resolve_primary_score_source("pick_decision_lab", "pick") == (
        MODEL_V4_DYNASTY_ASSET
    )

    with pytest.raises(UnknownScoreSourceError):
        resolve_primary_score_source("mystery_surface", "player")


def test_envelope_from_row_namespaces_legacy_private_score_as_comparison_only() -> None:
    env = envelope_from_row(
        {
            "asset_id": "player:keenan-allen",
            "display_name": "Keenan Allen",
            "private_score": "82.4",
            "source_path": (
                "local_exports/data_packs/lve_sleeper_20260505_pdf_ranks/model_outputs.csv"
            ),
            "model_version": "veteran_lve_stats_first_v1_0_0",
            "score_as_of_date": "2026-05-30",
            "confidence_cap": "0.7",
            "warnings": "legacy_formula_warning",
            "allowed_use": "legacy_comparison_context",
            "blocked_use": "primary_review_score",
        },
        score_column="private_score",
    )

    validated = validate_score_envelope(env)

    assert validated.primary_review_score is None
    assert validated.legacy_active_pack_score == 82.4
    assert validated.source_column == "private_score"
    assert validated.score_type == "legacy_active_pack_score"
    assert validated.lineage_class == "legacy_active_pack"


def test_export_preserves_score_disclosure_contract() -> None:
    validated = validate_score_envelope(_envelope())
    exported = export_score_disclosure(validated)

    for field in (
        "source_path",
        "source_column",
        "model_version",
        "lineage_class",
        "asset_type",
        "score_as_of_date",
        "confidence_cap",
        "warnings",
        "market_display_only",
        "legacy_formula_warning",
        "manual_decision_required",
        "allowed_use",
        "blocked_use",
    ):
        assert field in exported
    assert exported["source_column"] == "checkpoint_review_score"
    assert exported["warnings"] == "team_mismatch/source_review"


def test_market_context_payload_is_display_only_and_blocks_primary_uses() -> None:
    row = {
        "player": "Example Player",
        "dynasty_startup_adp": 42.0,
        "market_gap_signal": "model_higher_than_market_watch",
        "projection_points": 123.4,
        "checkpoint_review_score": 55.0,
    }

    context = market_display_context(row)

    assert row_has_market_display_fields(row) is True
    assert context["market_display_only"] is True
    assert "primary_review_score" in str(context["blocked_use"])
    assert context["fields"] == {
        "dynasty_startup_adp": 42.0,
        "market_gap_signal": "model_higher_than_market_watch",
        "projection_points": 123.4,
    }
