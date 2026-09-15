from __future__ import annotations

from src.services.team_code_alias_service import TEAM_CODE_ALIASES, normalize_team_code


def test_normalize_team_code_resolves_the_real_fantasypros_jacksonville_alias() -> None:
    # Reconfirmed live this pass: FantasyPros' real K/DST consensus API
    # reports Jacksonville as "JAC"; Sleeper's real players/nfl catalog
    # reports it as "JAX". Both must normalize to the same canonical code.
    assert normalize_team_code("JAC") == "JAX"
    assert normalize_team_code("JAX") == "JAX"


def test_normalize_team_code_applies_every_documented_alias() -> None:
    for source, canonical in TEAM_CODE_ALIASES.items():
        assert normalize_team_code(source) == canonical


def test_normalize_team_code_is_case_and_whitespace_insensitive() -> None:
    assert normalize_team_code("jac") == "JAX"
    assert normalize_team_code(" Jac ") == "JAX"


def test_normalize_team_code_passes_unknown_codes_through_unchanged() -> None:
    assert normalize_team_code("SF") == "SF"
    assert normalize_team_code("NE") == "NE"
    assert normalize_team_code("XYZ") == "XYZ"


def test_normalize_team_code_handles_missing_values_without_guessing() -> None:
    assert normalize_team_code(None) == ""
    assert normalize_team_code("") == ""
