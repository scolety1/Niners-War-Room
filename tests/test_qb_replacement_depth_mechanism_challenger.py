from scripts.run_qb_replacement_depth_mechanism_challenger_v1 import (
    SYNTHETIC_QB_COUNT,
    SYNTHETIC_QB_STEP,
    SYNTHETIC_QB_TOP_POINTS,
    TEAM_COUNT,
    run,
)


def test_champion_uses_the_configured_depth_two_baseline() -> None:
    champion_qb, _challenger_qb, _rows = run()
    assert champion_qb.rostered_count == TEAM_COUNT * 2
    # Replacement is the next available QB beyond the top 32, i.e. QB #33
    # on the synthetic ladder (index 32, 0-based).
    expected = SYNTHETIC_QB_TOP_POINTS - SYNTHETIC_QB_STEP * (TEAM_COUNT * 2)
    assert champion_qb.replacement_points == expected


def test_challenger_uses_the_shallower_configured_depth_one_baseline() -> None:
    _champion_qb, challenger_qb, _rows = run()
    assert challenger_qb.rostered_count == TEAM_COUNT * 1
    # Replacement is the next available QB beyond the top 16, i.e. QB #17
    # (index 16, 0-based).
    expected = SYNTHETIC_QB_TOP_POINTS - SYNTHETIC_QB_STEP * (TEAM_COUNT * 1)
    assert challenger_qb.replacement_points == expected


def test_challenger_replacement_points_are_higher_than_championss() -> None:
    # A shallower configured depth means fewer bench QBs get rostered before
    # "next available" is reached, so the replacement baseline sits closer
    # to the starters -- exactly the direction the audit's root-cause
    # analysis predicts.
    champion_qb, challenger_qb, _rows = run()
    assert challenger_qb.replacement_points > champion_qb.replacement_points


def test_every_qbs_value_over_replacement_shrinks_under_the_challenger() -> None:
    _champion_qb, _challenger_qb, rows = run()
    assert len(rows) == SYNTHETIC_QB_COUNT
    for row in rows:
        assert row["challenger_vor"] <= row["champion_vor"]
        assert row["vor_delta_challenger_minus_champion"] <= 0.0
    # The very top QB should show a real, non-trivial shrink -- not a
    # rounding artifact.
    top_row = rows[0]
    assert top_row["champion_vor"] == 160.0
    assert top_row["challenger_vor"] == 80.0


def test_production_replacement_function_is_called_unmodified() -> None:
    # This is a structural guard, not a numeric one: the script must import
    # calculate_replacement_levels from the real production module and must
    # not define any local reimplementation of it.
    import inspect

    from scripts import run_qb_replacement_depth_mechanism_challenger_v1 as module

    source = inspect.getsource(module)
    assert "def calculate_replacement_levels" not in source
    assert "from src.services.redraft_engine_v1_service import" in source
