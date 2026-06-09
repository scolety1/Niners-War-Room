from __future__ import annotations

import csv
from pathlib import Path

from src.services.draft_prep_data_foundation_service import (
    EXPLICIT_2025_USER_DRAFTED,
    build_draft_prep_data_foundation,
)

OUTPUT_ROOT = Path("local_exports/model_v4/draft_prep/latest")
DOC_ROOT = Path("docs/model_v4")


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_draft_prep_foundation_outputs_and_guardrails() -> None:
    result = build_draft_prep_data_foundation()

    assert result.prior_history_rows > 0
    assert result.scouting_pool_ready is True
    assert result.confirmed_legal_pool_ready is False
    assert (OUTPUT_ROOT / "prior_league_draft_history_review_rows.csv").exists()
    assert (OUTPUT_ROOT / "prior_league_draft_behavior_summary.csv").exists()
    assert (OUTPUT_ROOT / "draftable_pool_source_readiness.csv").exists()
    assert (OUTPUT_ROOT / "scouting_prep_pool_review_rows.csv").exists()

    for name in (
        "DRAFT_PREP_CURRENT_STATE_AUDIT_20260609.md",
        "PRIOR_DRAFT_HISTORY_NORMALIZATION_20260609.md",
        "PRIOR_LEAGUE_DRAFT_BEHAVIOR_SUMMARY_20260609.md",
        "DRAFTABLE_POOL_SOURCE_CONTRACT_20260609.md",
        "DRAFTABLE_POOL_SOURCE_READINESS_20260609.md",
        "DRAFT_PREP_PICK_WINDOW_SPEC_20260609.md",
        "DRAFT_PREP_PAGE_ARCHITECTURE_20260609.md",
    ):
        assert (DOC_ROOT / name).exists()


def test_2025_user_drafted_list_and_yellow_highlights_are_context_only() -> None:
    rows = _rows(OUTPUT_ROOT / "prior_league_draft_history_review_rows.csv")
    drafted = {
        row["normalized_player_key"]
        for row in rows
        if row["draft_year"] == "2025" and row["user_drafted_flag"] == "true"
    }

    assert drafted == EXPLICIT_2025_USER_DRAFTED
    assert any(
        row["player"] == "Tyler Warren"
        and row["user_must_draft_at_cost_flag"] == "true"
        for row in rows
    )
    assert all(
        "NWR private value" in row["blocked_use"]
        for row in rows
        if row["user_must_draft_at_cost_flag"] == "true"
    )


def test_prior_history_and_scouting_pool_do_not_create_final_recommendations() -> None:
    prior_rows = _rows(OUTPUT_ROOT / "prior_league_draft_history_review_rows.csv")
    pool_rows = _rows(OUTPUT_ROOT / "scouting_prep_pool_review_rows.csv")

    combined_text = "\n".join(
        "|".join(row.values()) for row in [*prior_rows[:50], *pool_rows[:50]]
    ).lower()
    assert "draft this player" not in combined_text
    assert "do_not_use_as_private_value" in combined_text or "nwr private value" in combined_text
    assert all("legacy_active_pack" not in row["lineage_class"] for row in pool_rows)


def test_draftable_readiness_preserves_missing_legal_sources_and_504_no_baseline() -> None:
    readiness = _rows(OUTPUT_ROOT / "draftable_pool_source_readiness.csv")
    dropped = next(row for row in readiness if row["source_area"] == "dropped/released veterans")
    assert dropped["readiness_status"] == "missing_required_for_legal_pool"

    active_rookie = next(
        row for row in readiness if row["source_area"] == "active confirmed legal draftable pool"
    )
    assert active_rookie["readiness_status"] == "missing_optional_or_inactive"

    pick_spec = (DOC_ROOT / "DRAFT_PREP_PICK_WINDOW_SPEC_20260609.md").read_text(
        encoding="utf-8"
    )
    assert "2026 5.04" in pick_spec
    assert "No Baseline" in pick_spec
    assert "no exact equivalence" in pick_spec
