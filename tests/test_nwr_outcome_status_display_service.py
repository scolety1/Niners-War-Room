from __future__ import annotations

from pathlib import Path

import pytest

from src.services.nwr_outcome_status_display_service import (
    build_default_app_status_registry,
    build_outcome_status_display,
    outcome_status_sort_value,
    write_sprint_5ah_status_only_exports,
)


def test_default_same_year_status_is_text_only_and_nonnumeric() -> None:
    display = build_outcome_status_display(target="same_year_starter")

    assert display.status_code == "in_development"
    assert display.status_label == "In development"
    assert display.probability_value is None
    assert display.probability_band is None
    assert display.sortable_value is None
    assert display.is_released is False
    assert display.is_numeric is False


def test_ready_internal_only_displays_as_unreleased() -> None:
    display = build_outcome_status_display(
        target="same_year_useful",
        evidence_status="ready_internal_only",
    )

    assert display.status_code == "ready_internal_only"
    assert display.status_label == "Internal only - not released"
    assert display.probability_value is None
    assert display.is_released is False
    assert display.is_numeric is False


def test_ready_released_is_not_reachable_from_status_only_adapter() -> None:
    with pytest.raises(ValueError, match="cannot request ready_released"):
        build_outcome_status_display(
            target="same_year_difference_maker",
            evidence_status="ready_released",
        )

    registry = build_default_app_status_registry()

    assert all(display.status_code != "ready_released" for display in registry)
    assert all(display.probability_value is None for display in registry)
    assert all(display.sortable_value is None for display in registry)


def test_next_year_and_hazard_targets_are_blocked_or_unreleased() -> None:
    next_year = build_outcome_status_display(target="next_year_starter")
    hazard = build_outcome_status_display(target="hazard_windows")

    assert next_year.status_code == "blocked_validation_gate"
    assert next_year.probability_value is None
    assert next_year.is_released is False
    assert hazard.status_code == "not_applicable"
    assert hazard.probability_value is None


def test_kickers_are_not_applicable() -> None:
    display = build_outcome_status_display(target="same_year_starter", position="K")

    assert display.status_code == "not_applicable"
    assert display.status_label == "Not applicable"
    assert display.probability_value is None


def test_rankings_cannot_sort_by_hidden_outcome_probability() -> None:
    display = build_outcome_status_display(target="same_year_replacement_or_bust")

    assert outcome_status_sort_value(display) is None
    assert display.sortable_value is None


def test_adapter_does_not_import_internal_model_outputs_or_read_exports() -> None:
    import src.services.nwr_outcome_status_display_service as service

    service_text = Path(service.__file__).read_text(encoding="utf-8")

    assert "nwr_outcome_internal_model_package_service" not in service_text
    assert "internal_logistic" not in service_text
    assert "read_csv" not in service_text
    assert "glob(" not in service_text
    assert "local_exports" not in service_text


def test_status_only_exports_create_no_app_readable_probability_table(tmp_path: Path) -> None:
    paths = write_sprint_5ah_status_only_exports(tmp_path)

    expected = {
        "status_only_app_contract",
        "status_only_target_display_registry",
        "app_surface_integration_audit",
        "blocked_numeric_probability_paths",
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


def test_status_only_exports_reject_app_and_ranking_paths(tmp_path: Path) -> None:
    for unsafe in (
        tmp_path / "app" / "outcome_status",
        tmp_path / "local_exports" / "rankings",
        tmp_path / "decision_board",
        tmp_path / "app_probability_table",
    ):
        with pytest.raises(ValueError, match="app|ranking"):
            write_sprint_5ah_status_only_exports(unsafe)


def test_app_and_ranking_logic_do_not_import_status_display_service() -> None:
    repo = Path(__file__).resolve().parents[1]
    searched_roots = [repo / "app", repo / "pages", repo / "streamlit_app.py"]
    forbidden = "nwr_outcome_status_display_service"
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
