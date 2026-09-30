from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import pytest

from src.services.draft_prep_data_foundation_service import (
    EXPLICIT_2025_USER_DRAFTED,
    PACKAGE_ROOT,
    DraftPrepSourcePackageMissingError,
    build_draft_prep_data_foundation,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKED_PATHS = ("docs/model_v4", "local_exports/model_v4")


def _tracked_git_status() -> str:
    """git status --porcelain restricted to the real tracked paths this service
    writes to, so tests can prove they never touched them."""
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", *TRACKED_PATHS],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


@pytest.fixture(autouse=True, scope="module")
def _tracked_docs_must_stay_untouched():
    """P0 regression guard: nothing in this test file may mutate the real
    tracked docs/model_v4 or local_exports/model_v4 content, no matter what any
    individual test below does. This is the defense-in-depth half of the fix;
    the production fail-closed check in build_draft_prep_data_foundation() is
    the other half.
    """
    before = _tracked_git_status()
    yield
    after = _tracked_git_status()
    assert before == after, (
        "tests/test_draft_prep_data_foundation_service.py modified tracked "
        "docs/model_v4 or local_exports/model_v4 content - this must never "
        f"happen.\ngit status before:\n{before}\ngit status after:\n{after}"
    )


@pytest.fixture(scope="module")
def foundation(tmp_path_factory: pytest.TempPathFactory):
    """Build the real draft-prep data foundation, isolated to tmp output/doc
    roots so the real tracked paths are never touched. Skips (rather than
    silently passing on degraded data) when the real source package is absent
    in this environment - see tests/hermetic_localdata_manifest.json.
    """
    if not PACKAGE_ROOT.exists():
        pytest.skip(
            "real prior-draft-history source package "
            f"({PACKAGE_ROOT}) is not present in this environment; skipping "
            "rather than exercising build_draft_prep_data_foundation() on "
            "degraded/absent source data"
        )
    output_root = tmp_path_factory.mktemp("draft_prep_output")
    doc_root = tmp_path_factory.mktemp("draft_prep_docs")
    result = build_draft_prep_data_foundation(output_root=output_root, doc_root=doc_root)
    return result, output_root, doc_root


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_draft_prep_foundation_outputs_and_guardrails(foundation) -> None:
    result, output_root, doc_root = foundation

    assert result.prior_history_rows > 0
    assert result.scouting_pool_ready is True
    assert result.confirmed_legal_pool_ready is False
    assert (output_root / "prior_league_draft_history_review_rows.csv").exists()
    assert (output_root / "prior_league_draft_behavior_summary.csv").exists()
    assert (output_root / "draftable_pool_source_readiness.csv").exists()
    assert (output_root / "scouting_prep_pool_review_rows.csv").exists()

    for name in (
        "DRAFT_PREP_CURRENT_STATE_AUDIT_20260609.md",
        "PRIOR_DRAFT_HISTORY_NORMALIZATION_20260609.md",
        "PRIOR_LEAGUE_DRAFT_BEHAVIOR_SUMMARY_20260609.md",
        "DRAFTABLE_POOL_SOURCE_CONTRACT_20260609.md",
        "DRAFTABLE_POOL_SOURCE_READINESS_20260609.md",
        "DRAFT_PREP_PICK_WINDOW_SPEC_20260609.md",
        "DRAFT_PREP_PAGE_ARCHITECTURE_20260609.md",
    ):
        assert (doc_root / name).exists()


def test_2025_user_drafted_list_and_yellow_highlights_are_context_only(foundation) -> None:
    result, output_root, _doc_root = foundation
    rows = _rows(output_root / "prior_league_draft_history_review_rows.csv")
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


def test_prior_history_and_scouting_pool_do_not_create_final_recommendations(foundation) -> None:
    result, output_root, _doc_root = foundation
    prior_rows = _rows(output_root / "prior_league_draft_history_review_rows.csv")
    pool_rows = _rows(output_root / "scouting_prep_pool_review_rows.csv")

    combined_text = "\n".join(
        "|".join(row.values()) for row in [*prior_rows[:50], *pool_rows[:50]]
    ).lower()
    assert "draft this player" not in combined_text
    assert "do_not_use_as_private_value" in combined_text or "nwr private value" in combined_text
    assert all("legacy_active_pack" not in row["lineage_class"] for row in pool_rows)


def test_draftable_readiness_preserves_missing_legal_sources_and_504_no_baseline(
    foundation,
) -> None:
    result, output_root, doc_root = foundation
    readiness = _rows(output_root / "draftable_pool_source_readiness.csv")
    dropped = next(row for row in readiness if row["source_area"] == "dropped/released veterans")
    assert dropped["readiness_status"] == "missing_required_for_legal_pool"

    active_rookie = next(
        row for row in readiness if row["source_area"] == "active confirmed legal draftable pool"
    )
    assert active_rookie["readiness_status"] == "missing_optional_or_inactive"

    pick_spec = (doc_root / "DRAFT_PREP_PICK_WINDOW_SPEC_20260609.md").read_text(
        encoding="utf-8"
    )
    assert "2026 5.04" in pick_spec
    assert "No Baseline" in pick_spec
    assert "no exact equivalence" in pick_spec


def test_build_fails_closed_when_source_package_is_missing() -> None:
    """P0 regression: if the real prior-draft-history source package is absent,
    build_draft_prep_data_foundation() must raise rather than silently writing a
    degraded/empty result over tracked docs - even when called with NO
    output_root/doc_root override, i.e. the real production/default call path
    (see build_draft_prep_data_foundation()'s defaults and
    scripts/build_draft_prep_data_foundation.py, which calls it exactly this
    way).
    """
    if PACKAGE_ROOT.exists():
        pytest.skip(
            "real source package is present in this environment; the "
            "fail-closed path is instead proven deterministically by "
            "test_build_fails_closed_with_explicit_missing_package_root below"
        )

    before = _tracked_git_status()

    with pytest.raises(DraftPrepSourcePackageMissingError):
        build_draft_prep_data_foundation()

    after = _tracked_git_status()
    assert before == after == ""


def test_build_fails_closed_with_explicit_missing_package_root(tmp_path: Path) -> None:
    """Deterministic version of the fail-closed contract that holds regardless
    of whether this environment happens to have the real source package: an
    explicitly-missing package_root must raise before anything is written,
    even to the (isolated, tmp_path) output/doc roots.
    """
    missing_package = tmp_path / "does_not_exist" / "draft_prep_codex_package"
    output_root = tmp_path / "output"
    doc_root = tmp_path / "docs"

    with pytest.raises(DraftPrepSourcePackageMissingError):
        build_draft_prep_data_foundation(
            package_root=missing_package,
            output_root=output_root,
            doc_root=doc_root,
        )

    assert not output_root.exists()
    assert not doc_root.exists()


def test_build_fails_closed_when_package_present_but_has_no_real_inputs(tmp_path: Path) -> None:
    """An empty/placeholder package directory (present but with no *.xlsx and no
    PDF transcription CSV) must also fail closed rather than being treated as a
    genuine zero-row source.
    """
    empty_package = tmp_path / "draft_prep_codex_package"
    (empty_package / "raw_uploaded_files").mkdir(parents=True)
    output_root = tmp_path / "output"
    doc_root = tmp_path / "docs"

    with pytest.raises(DraftPrepSourcePackageMissingError):
        build_draft_prep_data_foundation(
            package_root=empty_package,
            output_root=output_root,
            doc_root=doc_root,
        )

    assert not output_root.exists()
    assert not doc_root.exists()
