from pathlib import Path

from src.services.model_v4_rotowire_identity_coverage_service import (
    build_rotowire_identity_coverage,
    write_rotowire_identity_coverage_outputs,
)


def test_rotowire_identity_coverage_resolves_truth_set_aliases() -> None:
    result = build_rotowire_identity_coverage()
    by_player = {row["truth_player_name"]: row for row in result.rows}

    btj = by_player["Brian Thomas Jr."]
    assert btj["coverage_status"] == "covered"
    assert btj["matched_source_names"] == "Brian Thomas"
    assert int(btj["player_stats_rows"]) > 0
    assert int(btj["projection_rows"]) == 1

    aiyuk = by_player["Brandon Aiyuk"]
    assert aiyuk["coverage_status"] == "covered"
    assert int(aiyuk["injury_rows"]) == 1
    assert int(aiyuk["depth_chart_rows"]) == 1


def test_rotowire_identity_coverage_writes_outputs(tmp_path: Path) -> None:
    result = build_rotowire_identity_coverage()
    paths = write_rotowire_identity_coverage_outputs(tmp_path, result)

    assert paths["coverage"].exists()
    assert paths["summary"].exists()
    assert "Brian Thomas Jr." in paths["coverage"].read_text(encoding="utf-8")
    assert result.summary["model_scores_changed"] is False
