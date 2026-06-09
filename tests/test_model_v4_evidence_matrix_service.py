from __future__ import annotations

import csv
import json

import pytest

from src.services.model_v4_evidence_matrix_service import (
    BACKTEST_MATRIX_HEADER,
    COVERAGE_HEADER,
    CURRENT_PROSPECT_IDENTITY_ADMISSION_NOTES_HEADER,
    NFL_MATRIX_HEADER,
    PROSPECT_MATRIX_HEADER,
    WARNING_HEADER,
    WORKOUT_ZERO_PLACEHOLDER_FIELDS,
    build_evidence_matrices,
    load_formula_admitted_prospect_rows,
    require_formula_admitted_prospect_rows,
    write_evidence_matrix_outputs,
)


@pytest.fixture(scope="module")
def evidence_result():
    return build_evidence_matrices()


def test_phase_10g_builds_all_required_matrices_without_scores(evidence_result) -> None:
    assert evidence_result.summary["nfl_player_rows"] == 80
    assert evidence_result.summary["current_prospect_rows"] > 50
    assert evidence_result.summary["admitted_current_prospect_identity_rows"] > 150
    assert evidence_result.summary["admitted_prospect_feature_rows"] == evidence_result.summary[
        "admitted_current_prospect_identity_rows"
    ]
    assert evidence_result.summary["review_current_prospect_identity_rows"] > 0
    assert evidence_result.summary["historical_backtest_rows"] > 300
    assert evidence_result.summary["formula_scores_calculated"] is False
    assert evidence_result.summary["final_rankings_calculated"] is False
    assert evidence_result.summary["market_leakage_violations"] == 0
    assert evidence_result.summary["duplicate_entity_rows"] == 0
    assert evidence_result.summary["fake_zero_missing_violations"] == 0
    assert evidence_result.summary["workout_zero_placeholder_violations"] == 0
    assert evidence_result.summary["ambiguous_join_rows"] == 0
    assert evidence_result.summary["historical_post_draft_college_evidence_violations"] == 0


def test_nfl_matrix_separates_factual_derived_and_market_context(evidence_result) -> None:
    bijan = _row_by(evidence_result.nfl_rows, "player_name", "Bijan Robinson")
    factual = json.loads(str(bijan["factual_evidence_json"]))
    derived = json.loads(str(bijan["derived_evidence_json"]))
    market = json.loads(str(bijan["market_context_fields_json"]))
    source_status = json.loads(str(bijan["source_status_json"]))

    assert "manual_first_downs" in factual
    assert "stats_first_component_evidence" in derived
    assert "replacement_vorp_review" not in derived
    assert "review_only_replacement_vorp" in json.loads(str(bijan["context_fields_json"]))
    assert "market_and_projection_context" in market
    assert source_status["prospect_prior_evidence"] == "not_applicable"
    assert "overall_candidate_rank" not in bijan
    assert "dynasty_candidate_value" not in bijan


def test_current_prospect_matrix_keeps_market_out_of_private_lanes(evidence_result) -> None:
    love = _row_by(evidence_result.prospect_rows, "prospect_name", "Jeremiyah Love")
    factual_text = str(love["factual_evidence_json"]).lower()
    derived_text = str(love["derived_evidence_json"]).lower().replace("market_share", "marketshare")
    prior_text = str(love["prospect_prior_evidence_json"]).lower()
    market = json.loads(str(love["market_context_fields_json"]))

    assert "adp" not in factual_text
    assert "adp" not in derived_text
    assert "big_board" not in factual_text
    assert "big_board" not in derived_text
    assert "rookie_adp" in market
    assert "kaggle_consensus_big_board" in market
    assert "workout_profile" in prior_text or "recruiting_profile" in prior_text
    assert love["identity_status"] == "admitted_exact_name_position_college_draft_year"
    assert love["formula_identity_admitted"] is True
    assert love["excluded_reason"] == ""
    assert "source_normalized_review_not_formula_admitted" not in str(love["warning_flags"])


def test_current_prospect_matrix_explicitly_blocks_review_only_rows(
    evidence_result,
) -> None:
    review_rows = [
        row
        for row in evidence_result.prospect_rows
        if row["identity_status"] == "source_normalized_review_not_formula_admitted"
    ]
    assert len(review_rows) == evidence_result.summary["review_current_prospect_identity_rows"]
    for row in review_rows:
        assert row["formula_identity_admitted"] is False
        assert row["excluded_reason"]
        assert "source_normalized_review_not_formula_admitted" in str(row["warning_flags"])


def test_formula_admitted_prospect_loader_fails_closed(
    evidence_result,
) -> None:
    admitted_rows = [
        row for row in evidence_result.prospect_rows if row["formula_identity_admitted"] is True
    ]
    review_row = next(
        row for row in evidence_result.prospect_rows if row["formula_identity_admitted"] is False
    )

    assert len(require_formula_admitted_prospect_rows(admitted_rows)) == len(admitted_rows)
    with pytest.raises(ValueError):
        require_formula_admitted_prospect_rows([review_row])

    row_without_gate = dict(admitted_rows[0])
    row_without_gate.pop("formula_identity_admitted")
    with pytest.raises(ValueError):
        require_formula_admitted_prospect_rows([row_without_gate])


def test_backtest_matrix_uses_pre_draft_features_and_draft_capital(evidence_result) -> None:
    cam_ward = _row_by(evidence_result.backtest_rows, "prospect_name", "Cameron Ward")
    assert cam_ward["draft_year"] == 2025
    assert cam_ward["draft_round"] == 1
    assert cam_ward["draft_pick"] == 1

    factual = json.loads(str(cam_ward["factual_evidence_json"]))
    prior = json.loads(str(cam_ward["prospect_prior_evidence_json"]))
    assert "college_production_summary" in factual
    assert prior["draft_capital"]["draft_pick"] == 1
    assert "rookie_adp" not in str(prior).lower()


def test_backtest_matrix_quarantines_duplicate_name_college_leakage(
    evidence_result,
) -> None:
    examples = {
        "Elijah Moore": (2021, "Florida State"),
        "Mason Taylor": (2025, "Tennessee Tech"),
        "Caleb Williams": (2024, "Pittsburgh"),
    }
    for player_name, (draft_year, bad_team) in examples.items():
        row = _row_by(evidence_result.backtest_rows, "prospect_name", player_name)
        assert row["draft_year"] == draft_year
        factual = json.loads(str(row["factual_evidence_json"]))
        derived = json.loads(str(row["derived_evidence_json"]))
        payload_text = json.dumps({"factual": factual, "derived": derived})
        assert bad_team not in payload_text
        assert "historical_college_evidence_after_draft_year_quarantined" in str(
            row["warning_flags"]
        )


def test_historical_backtest_has_no_post_draft_college_evidence(
    evidence_result,
) -> None:
    for row in evidence_result.backtest_rows:
        draft_year = int(row["draft_year"])
        factual = json.loads(str(row["factual_evidence_json"]))
        derived = json.loads(str(row["derived_evidence_json"]))
        for payload in _dict_payloads(factual.get("college_production_summary")):
            assert int(payload.get("final_college_season", 0)) < draft_year
        for field in ("college_season_latest", "college_targets_latest"):
            payload = factual.get(field)
            if payload:
                assert int(payload.get("season") or payload.get("year") or 0) < draft_year
        for payload in _dict_payloads(derived.get("college_market_share")):
            assert int(payload.get("season", 0)) < draft_year


def test_private_evidence_has_no_raw_rank_fields(evidence_result) -> None:
    for row in (
        *evidence_result.nfl_rows,
        *evidence_result.prospect_rows,
        *evidence_result.backtest_rows,
    ):
        for field in (
            "factual_evidence_json",
            "derived_evidence_json",
            "prospect_prior_evidence_json",
        ):
            payload = json.loads(str(row[field]))
            assert not _contains_key(payload, "rank")


def test_coverage_and_warning_matrices_have_expected_lanes(evidence_result) -> None:
    lanes = {row["lane"] for row in evidence_result.coverage_rows}
    assert {
        "scoring_evidence",
        "derived_evidence",
        "prospect_prior_evidence",
        "context_only",
        "market_context_only",
        "source_limited",
    }.issubset(lanes)

    coverage_by_group = {row["feature_group"] for row in evidence_result.coverage_rows}
    assert "manual_first_downs" in coverage_by_group
    assert "source_limited_combine" in coverage_by_group
    assert "market_context" in coverage_by_group

    warning_codes = {row["warning_code"] for row in evidence_result.warning_rows}
    assert "market_context_excluded_from_private_value" in warning_codes
    assert "third_party_combine_source_limited" in warning_codes
    assert "source_normalized_review_not_formula_admitted" in warning_codes


def test_workout_zero_placeholders_are_missing_not_bad_testing(
    evidence_result,
) -> None:
    repaired_rows = 0
    for row in (*evidence_result.prospect_rows, *evidence_result.backtest_rows):
        prior = json.loads(str(row["prospect_prior_evidence_json"]))
        workout_profile = prior.get("workout_profile", {})
        if not workout_profile:
            continue
        for field in WORKOUT_ZERO_PLACEHOLDER_FIELDS:
            assert workout_profile.get(field) != 0
        repaired_fields = workout_profile.get("zero_placeholder_fields_repaired", [])
        if repaired_fields:
            repaired_rows += 1
            assert workout_profile.get("missing_after_zero_repair") == repaired_fields
            for field in repaired_fields:
                assert workout_profile[field] is None
            assert "workout_metric_zero_placeholder_repaired" in str(row["warning_flags"])
            assert "workout_metric_missing_after_zero_repair" in str(row["warning_flags"])

    assert repaired_rows > 0
    warning_codes = {row["warning_code"] for row in evidence_result.warning_rows}
    assert "workout_metric_zero_placeholder_repaired" in warning_codes
    assert "workout_metric_missing_after_zero_repair" in warning_codes


def test_workout_height_strings_are_not_typed_as_zero(
    evidence_result,
) -> None:
    love_row = next(
        row for row in evidence_result.prospect_rows if row["prospect_name"] == "Jeremiyah Love"
    )
    prior = json.loads(str(love_row["prospect_prior_evidence_json"]))
    workout_profile = prior["workout_profile"]

    assert workout_profile["height"] == "6-0"
    assert workout_profile["height_inches"] == 72
    assert "height" not in workout_profile.get("zero_placeholder_fields_repaired", [])


def test_college_evidence_coverage_is_prospect_prior_not_scoring(
    evidence_result,
) -> None:
    for row in evidence_result.coverage_rows:
        if row["feature_group"] not in {"college_production", "college_market_share"}:
            continue
        if row["matrix_name"] not in {
            "prospect_current_feature_matrix",
            "historical_rookie_backtest_feature_matrix",
        }:
            continue
        assert row["lane"] == "prospect_prior_evidence"
        if row["present"]:
            assert "formula_admitted_after_validation" in str(row["source_status"])


def test_write_evidence_matrix_outputs(tmp_path, evidence_result) -> None:
    doc_path = tmp_path / "PHASE_10G_EVIDENCE_MATRICES.md"
    paths = write_evidence_matrix_outputs(
        output_root=tmp_path,
        doc_path=doc_path,
        result=evidence_result,
    )

    for path in (
        paths.nfl,
        paths.prospects,
        paths.admitted_prospect_features,
        paths.backtest,
        paths.coverage,
        paths.warnings,
        paths.admitted_prospects,
        paths.prospect_identity_review,
        paths.prospect_identity_notes,
        paths.summary,
        paths.doc,
    ):
        assert path.exists()

    assert _header(paths.nfl) == list(NFL_MATRIX_HEADER)
    assert _header(paths.prospects) == list(PROSPECT_MATRIX_HEADER)
    assert _header(paths.admitted_prospect_features) == list(PROSPECT_MATRIX_HEADER)
    assert _header(paths.backtest) == list(BACKTEST_MATRIX_HEADER)
    assert _header(paths.coverage) == list(COVERAGE_HEADER)
    assert _header(paths.warnings) == list(WARNING_HEADER)
    assert _header(paths.prospect_identity_notes) == list(
        CURRENT_PROSPECT_IDENTITY_ADMISSION_NOTES_HEADER
    )
    assert "No active rankings" in paths.doc.read_text(encoding="utf-8")
    admitted_text = paths.admitted_prospects.read_text(encoding="utf-8")
    admitted_features = load_formula_admitted_prospect_rows(paths.admitted_prospect_features)
    admitted_feature_keys = {row["canonical_prospect_key"] for row in admitted_features}
    with paths.admitted_prospects.open(encoding="utf-8") as handle:
        admitted_identity_keys = {
            row["canonical_prospect_key"] for row in csv.DictReader(handle)
        }
    review_text = paths.prospect_identity_review.read_text(encoding="utf-8")
    notes_text = paths.prospect_identity_notes.read_text(encoding="utf-8")
    assert "Jeremiyah Love" in admitted_text
    assert "source_normalized_review_not_formula_admitted" in review_text
    assert admitted_feature_keys == admitted_identity_keys
    assert "source_normalized_review_not_formula_admitted" not in (
        paths.admitted_prospect_features.read_text(encoding="utf-8")
    )
    assert "admitted" in notes_text
    assert "review_only" in notes_text


def _row_by(rows: tuple[dict[str, object], ...], field: str, value: object) -> dict[str, object]:
    matches = [row for row in rows if row[field] == value]
    assert len(matches) == 1
    return matches[0]


def _header(path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        return next(reader)


def _dict_payloads(value) -> list[dict]:
    if not isinstance(value, dict):
        return []
    return [item for item in value.values() if isinstance(item, dict)]


def _contains_key(value, target: str) -> bool:
    if isinstance(value, dict):
        return any(key == target or _contains_key(item, target) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_key(item, target) for item in value)
    return False
