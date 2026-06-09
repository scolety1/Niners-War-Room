from __future__ import annotations

from pathlib import Path

from src.services.rankings_post_patch_acceptance_service import (
    build_rankings_post_patch_acceptance,
    write_rankings_post_patch_acceptance,
)


def test_post_patch_acceptance_summary_passes_core_gates() -> None:
    result = build_rankings_post_patch_acceptance()

    assert result.summary["active_rows"] == 240
    assert result.summary["qb_rb_wr_te_rows"] == 232
    assert result.summary["kicker_rows"] == 8
    assert result.summary["nwr_scored_rows"] == 232
    assert result.summary["no_private_score_rows"] == 8
    assert result.summary["source_quarantine_non_kickers"] == 0
    assert result.summary["rb_wr_unchanged"] is True
    assert result.summary["sentinels_safe"] is True
    assert result.summary["contamination_safe"] is True
    assert result.summary["failed_acceptance_criteria"] == []
    assert result.summary["verdict"] == "rankings_accepted_for_human_review"


def test_post_patch_acceptance_shape_is_rankings_review_safe() -> None:
    result = build_rankings_post_patch_acceptance()
    top25 = result.top_100_rows[:25]
    top10 = result.top_100_rows[:10]

    assert not any(row["position"] == "QB" for row in top10)
    assert top25[0]["position"] != "TE"
    assert any(row["position"] == "TE" for row in top25)
    assert sum(1 for row in top25 if row["position"] == "QB") <= 3


def test_post_patch_review_csvs_have_required_content() -> None:
    result = build_rankings_post_patch_acceptance()

    assert len(result.top_100_rows) == 100
    assert len(result.my_team_rows) == 24
    assert {row["position"] for row in result.qb_te_rows} == {"QB", "TE"}
    assert any(row["player"] == "Trey McBride" for row in result.qb_te_rows)
    assert any(row["player"] == "Josh Allen" for row in result.qb_te_rows)


def test_post_patch_acceptance_reports_include_final_decision_boundaries() -> None:
    result = build_rankings_post_patch_acceptance()

    assert "Decision Board should remain blocked" in result.acceptance_report
    assert "2026 Draft Board / Rookie Draft page" in result.acceptance_report
    assert "Market Rank and League Rank remain display-only" in result.acceptance_report
    assert "Rankings accepted for human review: True" in result.final_handoff


def test_write_post_patch_acceptance_outputs(tmp_path: Path) -> None:
    paths = write_rankings_post_patch_acceptance(
        top_100_path=tmp_path / "top.csv",
        my_team_path=tmp_path / "team.csv",
        qb_te_path=tmp_path / "qb_te.csv",
        acceptance_report_path=tmp_path / "acceptance.md",
        final_handoff_path=tmp_path / "handoff.md",
    )

    for path in (
        paths.top_100,
        paths.my_team,
        paths.qb_te,
        paths.acceptance_report,
        paths.final_handoff,
    ):
        assert path.exists()
    assert "nwr_rank" in paths.top_100.read_text(encoding="utf-8")
    assert "previous_rank_if_available" in paths.my_team.read_text(encoding="utf-8")
