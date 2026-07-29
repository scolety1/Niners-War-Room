from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import pytest

from src.services import outcome_v3_calibration_service as outcome

ROOT = Path(__file__).resolve().parents[1]


def _schema() -> pd.DataFrame:
    inventory = outcome.current_outcome_authority_inventory(ROOT)
    return outcome.outcome_v3_schema(inventory, as_of_year=2026)


def _panel_row(
    player_id: str,
    position: str,
    season: int,
    finish: float | str,
    *,
    evidence: str = "",
    name_join_used: bool = False,
) -> dict[str, object]:
    return {
        "substrate_row_id": f"{player_id}:{season}",
        "player_id": player_id,
        "target_player_name": f"{position} Player",
        "position": position,
        "anchor_season": season,
        "feature_season": season - 1,
        "label_next_position_finish": finish,
        "pyf_prior_rank_position_feature_season": 10,
        "pyf_prior_nwr_points": 150.0,
        "prior_games": 17,
        "age": 25.0,
        "age_cohort": "age_23_to_25",
        "low_games": False,
        "productive_veteran": False,
        "early_career": True,
        "outcome_evidence_status": evidence,
        "name_join_used": name_join_used,
    }


def _synthetic_panel() -> pd.DataFrame:
    rows = [
        _panel_row("qb-1", "QB", 2022, 5),
        _panel_row("qb-1", "QB", 2023, 5),
        # 2024 is intentionally missing.
        _panel_row("qb-1", "QB", 2025, 5),
        _panel_row("rb-1", "RB", 2023, 20),
        _panel_row("wr-1", "WR", 2023, 20),
        _panel_row("te-1", "TE", 2023, 10),
    ]
    return pd.DataFrame(rows)


def _target(
    targets: pd.DataFrame,
    player_id: str,
    season: int,
    field_id: str,
) -> pd.Series:
    return targets.loc[
        targets["player_id"].eq(player_id)
        & targets["anchor_season"].eq(season)
        & targets["field_id"].eq(field_id)
    ].iloc[0]


def test_current_authority_and_v3_schema_are_exact() -> None:
    inventory = outcome.current_outcome_authority_inventory(ROOT)
    schema = outcome.outcome_v3_schema(inventory, as_of_year=2026)
    governed = schema.loc[
        schema["schema_record_type"].eq("OUTCOME_V3_GOVERNED")
    ]
    aliases = schema.loc[schema["schema_record_type"].eq("LEGACY_V1_ALIAS")]

    assert len(inventory) == 43
    assert inventory["schema_record_type"].eq("LEGACY_V1_ALIAS").sum() == 7
    assert inventory["schema_record_type"].eq("CURRENT_GOVERNED").sum() == 36
    assert len(schema) == 79
    assert len(governed) == 72
    assert len(aliases) == 7
    assert set(aliases["compatibility_target"]).issubset(
        set(governed["internal_name"])
    )
    assert outcome.dynamic_horizon_label("THIS_YEAR", 2026) == "2026"
    assert outcome.dynamic_horizon_label("NEXT_YEAR", 2026) == "2027"
    assert outcome.dynamic_horizon_label("T_PLUS_2", 2026) == "2028"
    assert governed.loc[
        governed["relative_horizon"].eq("TWO_OF_NEXT_3Y"),
        "display_location",
    ].eq("Player Compare expanded only").all()


def test_relationship_graph_contains_all_required_partial_orders() -> None:
    edges = outcome.relationship_edges(_schema())
    pairs = set(zip(edges["narrower_field"], edges["broader_field"], strict=True))

    assert ("RB_T6_THIS_YEAR", "RB_T6_WITHIN_3Y") in pairs
    assert ("RB_T6_NEXT_YEAR", "RB_T6_WITHIN_3Y") in pairs
    assert ("RB_T6_T_PLUS_2", "RB_T6_WITHIN_3Y") in pairs
    assert ("RB_T6_WITHIN_3Y", "RB_T6_WITHIN_5Y") in pairs
    assert ("RB_T6_TWO_OF_NEXT_3Y", "RB_T6_WITHIN_3Y") in pairs
    assert ("RB_T6_THIS_YEAR", "RB_T12_THIS_YEAR") in pairs


def test_missing_player_season_and_future_censoring_never_become_failures() -> None:
    targets = outcome.build_historical_targets(_synthetic_panel(), _schema())
    missing_exact = _target(targets, "qb-1", 2023, "QB_T6_NEXT_YEAR")
    future_exact = _target(targets, "qb-1", 2023, "QB_T6_T_PLUS_2")
    early_positive = _target(targets, "qb-1", 2023, "QB_T6_WITHIN_5Y")

    assert math.isnan(missing_exact["target_label"])
    assert missing_exact["target_state"] == "insufficient"
    assert future_exact["target_label"] == 1
    assert early_positive["target_label"] == 1
    assert early_positive["positive_before_censoring"]
    assert early_positive["label_available_season"] == 2023


def test_two_of_three_requires_two_observed_hits_but_allows_positive_with_a_gap() -> None:
    targets = outcome.build_historical_targets(_synthetic_panel(), _schema())
    two_hits = _target(
        targets,
        "qb-1",
        2023,
        "QB_T6_TWO_OF_NEXT_3Y",
    )
    one_hit = _target(
        targets,
        "qb-1",
        2022,
        "QB_T6_TWO_OF_NEXT_3Y",
    )

    assert two_hits["target_label"] == 1
    assert two_hits["observed_hit_count"] == 2
    assert two_hits["positive_before_censoring"]
    assert one_hit["target_label"] == 1
    assert one_hit["observed_hit_count"] == 2

    changed = _synthetic_panel().copy()
    changed.loc[
        changed["player_id"].eq("qb-1") & changed["anchor_season"].eq(2025),
        "label_next_position_finish",
    ] = 20
    changed_targets = outcome.build_historical_targets(changed, _schema())
    insufficient = _target(
        changed_targets,
        "qb-1",
        2023,
        "QB_T6_TWO_OF_NEXT_3Y",
    )
    assert math.isnan(insufficient["target_label"])
    assert insufficient["target_state"] == "insufficient"


def test_explicit_inactive_is_observable_negative_and_removal_is_insufficient() -> None:
    panel = _synthetic_panel()
    inactive = _panel_row(
        "qb-1",
        "QB",
        2024,
        "",
        evidence="explicit_inactive_season",
    )
    panel = pd.concat([panel, pd.DataFrame([inactive])], ignore_index=True)
    targets = outcome.build_historical_targets(panel, _schema())
    exact = _target(targets, "qb-1", 2023, "QB_T6_NEXT_YEAR")

    assert exact["target_label"] == 0
    assert exact["inactive_evidence_count"] == 1

    panel.loc[
        panel["player_id"].eq("qb-1") & panel["anchor_season"].eq(2024),
        "outcome_evidence_status",
    ] = ""
    without_authority = outcome.build_historical_targets(panel, _schema())
    exact_without = _target(
        without_authority,
        "qb-1",
        2023,
        "QB_T6_NEXT_YEAR",
    )
    assert math.isnan(exact_without["target_label"])


def test_target_mutations_are_rejected_through_real_contract_validation() -> None:
    schema = _schema()
    targets = outcome.build_historical_targets(_synthetic_panel(), schema)

    missing_to_failure = targets.copy()
    mask = (
        missing_to_failure["player_id"].eq("qb-1")
        & missing_to_failure["anchor_season"].eq(2023)
        & missing_to_failure["field_id"].eq("QB_T6_NEXT_YEAR")
    )
    missing_to_failure.loc[mask, "target_label"] = 0
    missing_to_failure.loc[mask, "negative_complete"] = True
    missing_to_failure.loc[mask, "label_available_season"] = 2024
    with pytest.raises(AssertionError, match="converted to negative"):
        outcome.validate_target_contract(missing_to_failure, schema)

    censored_to_failure = targets.copy()
    mask = (
        censored_to_failure["player_id"].eq("rb-1")
        & censored_to_failure["field_id"].eq("RB_T6_WITHIN_5Y")
    )
    censored_to_failure.loc[mask, "target_label"] = 0
    censored_to_failure.loc[mask, "negative_complete"] = True
    censored_to_failure.loc[mask, "label_available_season"] = 2027
    with pytest.raises(AssertionError, match="converted to negative"):
        outcome.validate_target_contract(censored_to_failure, schema)

    offset = targets.copy()
    offset.loc[offset["field_id"].eq("WR_T12_T_PLUS_2"), "horizon"] = "NEXT_YEAR"
    with pytest.raises(AssertionError, match="target horizon drift"):
        outcome.validate_target_contract(offset, schema)

    window = targets.copy()
    window.loc[
        window["field_id"].eq("TE_T6_WITHIN_3Y"),
        "scheduled_label_available_season",
    ] += 1
    with pytest.raises(AssertionError, match="offset/window drift"):
        outcome.validate_target_contract(window, schema)

    two_of_three = targets.copy()
    two_of_three.loc[
        two_of_three["field_id"].eq("QB_T6_TWO_OF_NEXT_3Y"),
        "minimum_qualifying_seasons",
    ] = 1
    with pytest.raises(AssertionError, match="qualifying-season rule drift"):
        outcome.validate_target_contract(two_of_three, schema)


def test_name_join_and_future_label_mutations_fail_closed() -> None:
    panel = _synthetic_panel()
    panel.loc[0, "name_join_used"] = True
    with pytest.raises(AssertionError, match="name join"):
        outcome.build_historical_targets(panel, _schema())

    valid = pd.DataFrame(
        [
            {
                "base_train_max_label_available": 2020,
                "decision_feature_season": 2020,
                "prediction_origin": "nested_chronological_out_of_fold",
            }
        ]
    )
    outcome.validate_temporal_prediction_contract(valid)
    future = valid.copy()
    future["base_train_max_label_available"] = 2021
    with pytest.raises(AssertionError, match="future Outcome label leakage"):
        outcome.validate_temporal_prediction_contract(future)
    random_split = valid.copy()
    random_split["prediction_origin"] = "random_split"
    with pytest.raises(AssertionError, match="random-split"):
        outcome.validate_temporal_prediction_contract(random_split)
    in_sample = valid.copy()
    in_sample["prediction_origin"] = "in_sample"
    with pytest.raises(AssertionError, match="in-sample"):
        outcome.validate_temporal_prediction_contract(in_sample)


def test_baseline_smoothing_and_shrink_contract_is_exact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outcome.validate_model_contract()
    train = pd.DataFrame(
        {
            "target_label": [1.0, 0.0, 1.0],
            "profile_bucket": ["near_threshold", "near_threshold", "other"],
        }
    )
    test = pd.DataFrame({"profile_bucket": ["near_threshold", "missing"]})
    probability = outcome._profile_baseline(train, test)  # noqa: SLF001
    prevalence = (2 + 1) / (3 + 2)

    assert probability[0] == pytest.approx((1 + 5 * prevalence) / (2 + 5))
    assert probability[1] == pytest.approx(prevalence)

    monkeypatch.setattr(outcome, "PROFILE_PRIOR_STRENGTH", 12.0)
    with pytest.raises(AssertionError, match="smoothing or profile-prior"):
        outcome.validate_model_contract()


def test_low_sample_isotonic_and_probability_bounds_fail_closed() -> None:
    calibration = pd.DataFrame(
        {
            "anchor_season": [2020, 2021, 2022, 2023],
            "raw_probability": [0.1, 0.2, 0.3, 0.4],
            "target_label": [0, 0, 0, 1],
        }
    )
    predicted, status = outcome.calibrated_probability(
        calibration,
        [0.2, 0.8],
        "C3_ISOTONIC_MONOTONIC",
    )

    assert status.startswith("BLOCKED_LOW_SAMPLE")
    assert predicted.tolist() == [0.2, 0.8]
    outcome.validate_probability_range([0.0, 0.5, 1.0])
    with pytest.raises(AssertionError, match=r"outside \[0,1\]"):
        outcome.validate_probability_range([0.2, 1.01])


def test_logical_mutations_are_detected_and_projection_is_burden_gated() -> None:
    frame = pd.DataFrame(
        [
            {
                "candidate": "C0_CURRENT_PROFILE_BUCKET_BASELINE",
                "substrate_row_id": "row",
                "field_id": "RB_T6_THIS_YEAR",
                "probability_pre_projection": 0.90,
            },
            {
                "candidate": "C0_CURRENT_PROFILE_BUCKET_BASELINE",
                "substrate_row_id": "row",
                "field_id": "RB_T12_THIS_YEAR",
                "probability_pre_projection": 0.10,
            },
            {
                "candidate": "C0_CURRENT_PROFILE_BUCKET_BASELINE",
                "substrate_row_id": "row",
                "field_id": "RB_T6_NEXT_YEAR",
                "probability_pre_projection": 0.70,
            },
            {
                "candidate": "C0_CURRENT_PROFILE_BUCKET_BASELINE",
                "substrate_row_id": "row",
                "field_id": "RB_T6_T_PLUS_2",
                "probability_pre_projection": 0.60,
            },
            {
                "candidate": "C0_CURRENT_PROFILE_BUCKET_BASELINE",
                "substrate_row_id": "row",
                "field_id": "RB_T6_WITHIN_3Y",
                "probability_pre_projection": 0.20,
            },
            {
                "candidate": "C0_CURRENT_PROFILE_BUCKET_BASELINE",
                "substrate_row_id": "row",
                "field_id": "RB_T6_WITHIN_5Y",
                "probability_pre_projection": 0.15,
            },
            {
                "candidate": "C0_CURRENT_PROFILE_BUCKET_BASELINE",
                "substrate_row_id": "row",
                "field_id": "RB_T6_TWO_OF_NEXT_3Y",
                "probability_pre_projection": 0.50,
            },
        ]
    )
    raw = outcome.logical_violations(
        frame, probability_column="probability_pre_projection"
    )
    projected, consistency = outcome.project_probabilities(frame)
    burden = outcome.projection_burden_results(projected)
    values = projected.set_index("field_id")["probability"]

    assert len(raw) >= 4
    assert consistency.loc[consistency["stage"].eq("governed"), "violation_count"].eq(
        0
    ).all()
    assert values["RB_T6_THIS_YEAR"] <= values["RB_T12_THIS_YEAR"]
    assert values["RB_T6_THIS_YEAR"] <= values["RB_T6_WITHIN_3Y"]
    assert values["RB_T6_WITHIN_3Y"] <= values["RB_T6_WITHIN_5Y"]
    assert values["RB_T6_TWO_OF_NEXT_3Y"] <= values["RB_T6_WITHIN_3Y"]
    assert burden["projection_burden_gate"].eq("FAIL").any()


def test_integration_pack_enforces_missing_wrong_position_blocked_and_rank_order() -> None:
    schema = _schema()
    board = pd.DataFrame(
        [
            {
                "player_id": "rb-complete",
                "player_name": "RB Complete",
                "position": "RB",
                "age": 24,
                "nwr_rank": 1,
            },
            {
                "player_id": "wr-missing",
                "player_name": "WR Missing",
                "position": "WR",
                "age": 23,
                "nwr_rank": 2,
            },
        ]
    )
    features = pd.DataFrame(
        [
            {
                "nwr_player_id": "rb-complete",
                "gsis_id": "gsis-rb",
                "position": "RB",
                "missing_input_state": "complete",
                "missing_reason": "",
            },
            {
                "nwr_player_id": "wr-missing",
                "gsis_id": "",
                "position": "WR",
                "missing_input_state": "insufficient",
                "missing_reason": "missing exact identity",
            },
        ]
    )
    fields = outcome.governed_field_specs(schema)["internal_name"]
    acceptance = pd.DataFrame(
        [
            {
                "field_id": canonical,
                "classification": (
                    outcome.BLOCKED_WEAK
                    if canonical == "RB_T6_WITHIN_5Y"
                    else outcome.KEEP_BASELINE
                ),
                "effective_calibrator": outcome.CALIBRATION_FAMILIES[0],
                "reason_code": "TEST",
                "baseline_rows": 300,
                "baseline_positive_events": 100,
                "baseline_negative_events": 200,
            }
            for canonical in fields
        ]
    )
    probabilities = pd.DataFrame(
        [
            {
                "nwr_player_id": "rb-complete",
                "field_id": canonical,
                "probability": 0.25,
                "projection_delta": 0.0,
                "selected_calibrator": outcome.CALIBRATION_FAMILIES[0],
            }
            for canonical in fields
            if canonical.startswith("RB_") and canonical != "RB_T6_WITHIN_5Y"
        ]
    )
    integration = outcome.build_integration_pack(
        board,
        features,
        probabilities,
        schema,
        acceptance,
    )

    rb_wr = integration.loc[
        integration["player_id"].eq("rb-complete")
        & integration["field_id"].eq("WR_T6_THIS_YEAR")
    ].iloc[0]
    missing = integration.loc[
        integration["player_id"].eq("wr-missing")
        & integration["field_id"].eq("WR_T6_THIS_YEAR")
    ].iloc[0]
    blocked = integration.loc[
        integration["player_id"].eq("rb-complete")
        & integration["field_id"].eq("RB_T6_WITHIN_5Y")
    ].iloc[0]

    assert rb_wr["probability_display"] == outcome.NOT_APPLICABLE
    assert missing["probability_display"] == outcome.NOT_ENOUGH_INFORMATION
    assert blocked["probability_display"] == outcome.NOT_ENOUGH_INFORMATION
    assert integration.drop_duplicates("player_id")["player_id"].tolist() == [
        "rb-complete",
        "wr-missing",
    ]

    numeric_blocked = integration.copy()
    mask = (
        numeric_blocked["player_id"].eq("rb-complete")
        & numeric_blocked["field_id"].eq("RB_T6_WITHIN_5Y")
    )
    numeric_blocked.loc[mask, "probability"] = 0.0
    with pytest.raises(AssertionError, match="blocked Outcome"):
        outcome.validate_integration_pack(numeric_blocked, board)
