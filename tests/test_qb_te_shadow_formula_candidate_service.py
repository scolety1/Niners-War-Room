from __future__ import annotations

from pathlib import Path

import pytest

from src.services.full_player_board_value_service import DEFAULT_FULL_PLAYER_BOARD_ROWS
from src.services.qb_te_shadow_formula_candidate_service import (
    MOVEMENT_HEADER,
    RANKING_HEADER,
    SUSPICIOUS_HEADER,
    VARIANT_IDS,
    build_qb_te_shadow_formula_candidate_experiment,
    write_qb_te_shadow_formula_candidate_experiment,
)

pytestmark = pytest.mark.skipif(
    not DEFAULT_FULL_PLAYER_BOARD_ROWS.exists(),
    reason="full-board Rankings baseline is required",
)


def test_shadow_experiment_preserves_active_baseline_hashes() -> None:
    result = build_qb_te_shadow_formula_candidate_experiment()

    assert result.summary["baseline_rows"] == 240
    assert result.summary["baseline_scored_rows"] == 232
    assert result.summary["baseline_k_rows"] == 8
    assert result.summary["baseline_hashes_match"] is True
    assert result.summary["sentinels_safe"] is True
    assert result.summary["contamination_safe"] is True


def test_shadow_variants_are_proposal_only_and_complete() -> None:
    result = build_qb_te_shadow_formula_candidate_experiment()

    assert {variant.variant_id for variant in result.variants} == set(VARIANT_IDS)
    for variant in result.variants:
        assert len(variant.ranking_rows) == 240
        assert variant.movement_rows
        assert variant.position_rows
        assert variant.my_team_rows
        assert variant.suspicious_rows
        assert all(row["variant_id"] == variant.variant_id for row in variant.ranking_rows)


def test_shadow_outputs_do_not_use_blocked_source_inputs() -> None:
    result = build_qb_te_shadow_formula_candidate_experiment()
    blocked = (
        "adp input",
        "startup input",
        "projection input",
        "trade calculator input",
        "legacy active-pack input",
        "public rank input",
        "market rank input",
        "league rank input",
        "rotowire projection input",
    )
    text = "\n".join(
        [
            result.manifest.lower(),
            result.plan_report.lower(),
            result.results_report.lower(),
            result.handoff_report.lower(),
        ]
    )

    assert not any(term in text for term in blocked)
    assert "not candidate inputs" in result.plan_report


def test_sentinels_remain_comparison_only_in_shadow_rows() -> None:
    result = build_qb_te_shadow_formula_candidate_experiment()

    for variant in result.variants:
        rows = {row["player"]: row for row in variant.ranking_rows}
        assert rows["Keenan Allen"]["nwr_score_baseline"] == 33.1581
        assert rows["Darius Slayton"]["nwr_score_baseline"] == 23.6148
        assert rows["Keenan Allen"]["changed_by_candidate_area"] == "unchanged_by_variant"
        assert rows["Darius Slayton"]["changed_by_candidate_area"] == "unchanged_by_variant"


def test_shadow_reports_do_not_create_final_recommendations() -> None:
    result = build_qb_te_shadow_formula_candidate_experiment()
    forbidden = ("trade", "cut", "draft", "buy", "sell", "start-sit", "start/sit")

    for variant in result.variants:
        for row in variant.suspicious_rows:
            action_text = (
                f"{row['candidate_classification']} {row['human_review_question']}"
            ).lower()
            assert not any(word in action_text for word in forbidden)


def test_write_shadow_experiment_creates_only_experiment_outputs(tmp_path: Path) -> None:
    result = build_qb_te_shadow_formula_candidate_experiment()
    paths = write_qb_te_shadow_formula_candidate_experiment(
        output_root=tmp_path / "qb_te_shadow",
        result=result,
    )

    assert paths.manifest.exists()
    assert paths.manifest.parent == tmp_path / "qb_te_shadow"
    for variant_id, files in paths.variant_files.items():
        assert variant_id in VARIANT_IDS
        assert _header(files["rankings"]) == RANKING_HEADER
        assert _header(files["movement"]) == MOVEMENT_HEADER
        assert _header(files["suspicious"]) == SUSPICIOUS_HEADER
        for path in files.values():
            assert tmp_path in path.parents
    assert "No active Rankings output" in paths.manifest.read_text(encoding="utf-8")


def _header(path: Path) -> tuple[str, ...]:
    first = path.read_text(encoding="utf-8").splitlines()[0]
    return tuple(first.split(","))
