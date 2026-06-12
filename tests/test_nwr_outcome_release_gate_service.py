from __future__ import annotations

from pathlib import Path

import pytest

from src.services.nwr_outcome_release_gate_service import (
    PROBABILITY_STATUS_CODES,
    RELEASE_GATES,
    assert_monotonic_same_year_probabilities,
    default_release_gates,
    evaluate_probability_status,
    write_sprint_5af_release_gate_contract,
)


def test_default_target_status_is_unreleased_and_null() -> None:
    result = evaluate_probability_status(target="same_year_starter")

    assert result.status_code == "in_development"
    assert result.probability_payload is None
    assert result.probability_band is None
    assert result.hidden_sortable_probability is None
    assert result.app_readable_payload is False


def test_any_failed_gate_blocks_probability_payload() -> None:
    gates = default_release_gates(True)
    gates["calibration_gate"] = False

    result = evaluate_probability_status(
        target="same_year_useful",
        release_gates=gates,
        requested_probability=0.42,
    )

    assert result.status_code == "blocked_calibration_gate"
    assert result.probability_payload is None
    assert result.hidden_sortable_probability is None
    assert result.app_readable_payload is False


def test_ready_released_requires_all_gates_true() -> None:
    result = evaluate_probability_status(
        target="same_year_difference_maker",
        release_gates=default_release_gates(True),
        requested_probability=0.12,
    )

    assert result.status_code == "ready_released"
    assert result.probability_payload == 0.12
    assert result.hidden_sortable_probability == 0.12
    assert result.app_readable_payload is True


def test_ready_released_requires_numeric_probability_payload() -> None:
    with pytest.raises(ValueError, match="requires a numeric probability"):
        evaluate_probability_status(
            target="same_year_difference_maker",
            release_gates=default_release_gates(True),
        )


def test_status_precedence_is_deterministic() -> None:
    gates = default_release_gates(True)
    gates["validation_gate"] = False
    gates["hq_approval_gate"] = False

    result = evaluate_probability_status(
        target="same_year_starter",
        release_gates=gates,
        requested_probability=0.50,
    )

    assert result.status_code == "blocked_validation_gate"


def test_probability_status_codes_include_required_values() -> None:
    required = {
        "in_development",
        "model_unavailable",
        "needs_data",
        "insufficient_evidence",
        "not_applicable",
        "blocked_leakage_gate",
        "blocked_validation_gate",
        "blocked_calibration_gate",
        "blocked_confidence_gate",
        "blocked_documentation_gate",
        "blocked_operational_gate",
        "blocked_hq_approval",
        "ready_internal_only",
        "ready_released",
    }

    assert required.issubset(set(PROBABILITY_STATUS_CODES))


def test_next_year_starter_remains_blocked() -> None:
    result = evaluate_probability_status(
        target="next_year_starter",
        release_gates=default_release_gates(True),
        requested_probability=0.33,
    )

    assert result.status_code == "blocked_validation_gate"
    assert result.probability_payload is None
    assert result.app_readable_payload is False


def test_ready_internal_only_is_not_app_ready() -> None:
    result = evaluate_probability_status(
        target="same_year_useful",
        evidence_status="ready_internal_only",
        requested_probability=0.66,
    )

    assert result.status_code == "ready_internal_only"
    assert result.probability_payload is None
    assert result.hidden_sortable_probability is None
    assert result.app_readable_payload is False


def test_kickers_return_not_applicable() -> None:
    result = evaluate_probability_status(
        target="same_year_starter",
        position="K",
        release_gates=default_release_gates(True),
        requested_probability=0.99,
    )

    assert result.status_code == "not_applicable"
    assert result.probability_payload is None


def test_monotonic_same_year_probabilities_required() -> None:
    assert_monotonic_same_year_probabilities(
        {
            "same_year_difference_maker": 0.10,
            "same_year_starter": 0.20,
            "same_year_useful": 0.35,
        }
    )

    with pytest.raises(ValueError, match="Difference-maker <= Starter <= Useful"):
        assert_monotonic_same_year_probabilities(
            {
                "same_year_difference_maker": 0.40,
                "same_year_starter": 0.20,
                "same_year_useful": 0.35,
            }
        )


def test_export_contract_creates_no_app_probability_or_player_export(tmp_path: Path) -> None:
    paths = write_sprint_5af_release_gate_contract(tmp_path)

    expected = {
        "release_gate_registry",
        "probability_status_codes",
        "target_release_registry_draft",
        "status_precedence_rules",
        "app_safe_display_contract",
        "blocked_probability_paths",
        "readme",
    }
    assert set(paths) == expected
    for path in paths.values():
        assert path.exists()

    forbidden_files = {
        "app_probability_table.csv",
        "player_probabilities.csv",
        "player_level_predictions.csv",
        "rankings.csv",
    }
    assert not forbidden_files.intersection({path.name for path in tmp_path.iterdir()})

    forbidden_headers = {"player_id", "player_name", "row_id", "per_player_probability"}
    for path in tmp_path.glob("*.csv"):
        header = path.read_text(encoding="utf-8").splitlines()[0].split(",")
        assert not forbidden_headers.intersection(header), path.name


def test_export_contract_rejects_app_and_ranking_output_paths(tmp_path: Path) -> None:
    for unsafe in (
        tmp_path / "app" / "outcome_probability",
        tmp_path / "local_exports" / "model_v4" / "current_value" / "latest",
        tmp_path / "local_exports" / "rankings",
        tmp_path / "app_probability_table",
    ):
        with pytest.raises(ValueError, match="app|ranking"):
            write_sprint_5af_release_gate_contract(unsafe)


def test_export_contract_does_not_consume_internal_model_output_paths() -> None:
    import src.services.nwr_outcome_release_gate_service as service

    service_text = Path(service.__file__).read_text(encoding="utf-8")

    assert "sprint_5z_expanded_internal_validation_package" not in service_text
    assert "sprint_5t_internal_logistic_package" not in service_text
    assert "internal_logistic_outcome_metrics" not in service_text


def test_app_and_ranking_logic_do_not_import_release_gate_service() -> None:
    repo = Path(__file__).resolve().parents[1]
    searched_roots = [repo / "app", repo / "pages", repo / "streamlit_app.py"]
    forbidden = "nwr_outcome_release_gate_service"
    offenders: list[str] = []

    for root in searched_roots:
        if root.is_file():
            files = [root]
        elif root.is_dir():
            files = list(root.rglob("*.py"))
        else:
            files = []
        for path in files:
            if forbidden in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(repo)))

    assert offenders == []


def test_unknown_gate_is_rejected() -> None:
    gates = {gate: True for gate in RELEASE_GATES}
    gates["surprise_gate"] = True

    with pytest.raises(ValueError, match="Unknown release gates"):
        evaluate_probability_status(target="same_year_starter", release_gates=gates)
