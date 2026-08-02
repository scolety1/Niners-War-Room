from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from src.services.disposable_worktree_cleanup_service import (
    KNOWN_GENERATED_PATHS,
    assess_disposable_worktree_cleanup,
)
from src.services.post_release_usability_service import (
    SCHEDULED_REFRESH_STATE,
    build_followup_dashboard,
    governed_source_freshness,
    initial_save_status,
    perform_workspace_write,
)
from src.services.trade_brief_export_service import (
    DISCLAIMER,
    TradeBriefValidationError,
    build_trade_brief,
)


def _decision(
    decision_id: str,
    follow_up_date: str,
    *,
    status: str = "Considered",
    created: str = "2026-08-01T12:00:00+00:00",
) -> dict[str, object]:
    return {
        "decision_id": decision_id,
        "decision_type": "trade considered",
        "status": status,
        "assets": ["current:p1"],
        "team_window": "Balanced",
        "follow_up_date": follow_up_date,
        "created_at_utc": created,
    }


def _assets() -> dict[str, dict[str, object]]:
    return {
        "current:p1": {
            "asset_name": "José Longname " + "X" * 300,
            "asset_type": "Current Player",
            "source_label": "Finished V1",
            "authority_status": "Production",
            "position": "WR",
            "team": "SF",
            "rank_label": "NWR Dynasty Rank",
            "rank_value": "12",
            "warnings": "",
        },
        "rookie:r1": {
            "asset_name": "Rookie One",
            "asset_type": "Rookie Review",
            "source_label": "Model V4 2026 Rookie Review",
            "authority_status": "Review-Only",
            "position": "RB",
            "team": "ARI",
            "rank_label": "Rookie Review Rank",
            "rank_value": "3",
            "warnings": "limited evidence",
        },
        "blocked-rookie:b1": {
            "asset_name": "Blocked Rookie",
            "asset_type": "Blocked Rookie",
            "source_label": "Model V4 2026 Rookie Review",
            "authority_status": "Blocked - Visible",
            "position": "TE",
            "team": "Not documented",
            "rank_label": "Not ranked",
            "rank_value": "999",
            "blocking_reason": "Identity authority missing",
        },
        "pick:2026:1.01": {
            "asset_name": "2026 1.01",
            "asset_type": "Draft Pick",
            "source_label": "Frozen 2026 Draft Context",
            "authority_status": "Context-Only",
            "position": "PICK",
            "team": "NWR",
            "rank_label": "Draft order",
            "rank_value": "1",
        },
    }


def test_freshness_is_explicit_and_never_uses_file_mtime(tmp_path: Path) -> None:
    marker = tmp_path / "source.csv"
    marker.write_text("x", encoding="utf-8")
    rows = governed_source_freshness(repo_root=tmp_path)
    assert SCHEDULED_REFRESH_STATE == "DISABLED_PENDING_OWNER_APPROVAL"
    assert any(row.state == "STALE" for row in rows)
    assert any(row.state == "REVIEW_ONLY" for row in rows)
    assert all(row.snapshot_date for row in rows)
    assert all(
        "scheduled refresh disabled" in row.refresh_status.casefold()
        or "automatic" in row.refresh_status.casefold()
        or "user save" in row.refresh_status.casefold()
        for row in rows
    )
    assert str(marker.stat().st_mtime) not in " ".join(row.snapshot_date for row in rows)


def test_missing_source_date_is_not_invented() -> None:
    rookie = next(row for row in governed_source_freshness() if "Rookie" in row.source_name)
    assert rookie.snapshot_date == "Not documented"


def test_save_state_orders_saving_before_verified_success() -> None:
    observed = []
    final = perform_workspace_write(lambda: "written", observer=observed.append)
    assert [row.state for row in observed] == ["Saving", "Saved"]
    assert final.result == "written"


def test_save_failure_never_emits_saved_and_requires_recovery_for_corruption() -> None:
    observed = []

    def fail() -> None:
        raise OSError("lock conflict")

    final = perform_workspace_write(fail, observer=observed.append)
    assert [row.state for row in observed] == ["Saving", "Save failed"]
    assert final.result is None
    assert initial_save_status("CORRUPT").state == "Recovery required"
    assert initial_save_status("MISSING").state == "Unsaved changes"


def test_blocked_write_result_never_emits_saved() -> None:
    class Blocked:
        status = "BLOCKED_CONFIRMATION_REQUIRED"
        message = "Confirm the action."

    observed = []
    final = perform_workspace_write(Blocked, observer=observed.append)
    assert [row.state for row in observed] == ["Saving", "Unsaved changes"]
    assert final.state != "Saved"


def test_followup_dashboard_classifies_all_neutral_buckets_and_filters() -> None:
    rows = [
        _decision("due", "2026-08-01"),
        _decision("overdue", "2026-07-31"),
        _decision("upcoming", "2026-08-02"),
        _decision("missing", ""),
        _decision("archived", "2026-08-01", status="Archived"),
    ]
    dashboard = build_followup_dashboard(rows, today=date(2026, 8, 1))
    assert [row["decision_id"] for row in dashboard.due_today] == ["due"]
    assert [row["decision_id"] for row in dashboard.overdue] == ["overdue"]
    assert [row["decision_id"] for row in dashboard.upcoming] == ["upcoming"]
    assert [row["decision_id"] for row in dashboard.missing_date] == ["missing"]
    assert [row["decision_id"] for row in dashboard.archived] == ["archived"]
    assert build_followup_dashboard(rows, today=date(2026, 8, 1), asset_query="p1").recent


def test_trade_brief_is_source_separated_unicode_safe_and_non_numeric_for_blocked_assets() -> None:
    brief = build_trade_brief(
        {
            "title": "Long Unicode Scenario — résumé",
            "created_at_utc": "2026-08-01T12:00:00+00:00",
            "side_a": ["current:p1", "blocked-rookie:b1"],
            "side_b": ["rookie:r1", "pick:2026:1.01"],
            "team_window": "Balanced",
            "rationale": "Manual roster construction context.",
        },
        assets=_assets(),
        personal={"current:p1": {"my_tier": "A", "tags": ["core"], "notes": "Keep context"}},
        include_personal=True,
    )
    payload = json.loads(brief.structured_json)
    assert DISCLAIMER in brief.markdown
    assert "José" in brief.markdown and "Personal tier: A" in brief.markdown
    blocked = next(row for row in payload["side_a"] if row["source_type"] == "Blocked Rookie")
    pick = next(row for row in payload["side_b"] if row["source_type"] == "Draft Pick")
    assert blocked["rank"] is None and pick["rank"] is None
    assert "Finished V1" in brief.markdown
    assert "Model V4 2026 Rookie Review" in brief.markdown
    assert "Frozen 2026 Draft Context" in brief.markdown


@pytest.mark.parametrize(
    "text",
    (
        "Please accept this",
        "Hidden trade winner",
        "This is unfair",
        "Create an automatic counteroffer",
    ),
)
def test_trade_brief_rejects_prohibited_recommendation_language(text: str) -> None:
    with pytest.raises(TradeBriefValidationError, match="prohibited recommendation"):
        build_trade_brief(
            {
                "title": "Manual scenario",
                "created_at_utc": "2026-08-01T12:00:00+00:00",
                "side_a": ["current:p1"],
                "side_b": ["rookie:r1"],
                "team_window": "Balanced",
                "rationale": text,
            },
            assets=_assets(),
        )


def test_trade_brief_keeps_missing_fields_visible() -> None:
    assets = _assets()
    assets["current:p1"].pop("rank_value")
    brief = build_trade_brief(
        {
            "title": "Manual scenario",
            "created_at_utc": "2026-08-01T12:00:00+00:00",
            "side_a": ["current:p1", "unknown"],
            "side_b": [],
            "team_window": "Custom/Unspecified",
            "rationale": "",
        },
        assets=assets,
    )
    assert "Missing source rank" in brief.markdown
    assert "Unknown asset" in brief.markdown


def test_applicable_pages_render_truthful_freshness_and_workspace_status() -> None:
    root = Path(__file__).resolve().parents[1]
    freshness_pages = (
        "00_command_center.py",
        "20_final_board_v1.py",
        "21_live_draft_room_v1.py",
        "22_player_compare_v1.py",
        "23_trading_lab_v1.py",
        "24_mock_draft_v1.py",
        "26_outcome_columns_v1.py",
        "28_settings_data_health_v1.py",
        "47_asset_explorer_v1.py",
        "48_rookie_board_review_v1.py",
    )
    for name in freshness_pages:
        text = (root / "app" / "pages" / name).read_text(encoding="utf-8")
        assert "render_source_freshness" in text
    for name in (
        "49_personal_board_v1.py",
        "50_decision_journal_v1.py",
        "51_saved_scenarios_v1.py",
    ):
        assert "render_save_status" in (root / "app" / "pages" / name).read_text(encoding="utf-8")


def test_cleanup_rejects_stable_operational_active_and_unique_source_paths() -> None:
    for protected in (r"C:\NWR\Niners-War-Room-V1", r"C:\NWR\Niners-War-Room"):
        result = assess_disposable_worktree_cleanup(
            protected,
            registered=True,
            patch_equivalent_in_hq=True,
        )
        assert not result.safe and "PRESERVED" in result.verdict
    active = assess_disposable_worktree_cleanup(
        r"C:\NWR\disposable",
        registered=True,
        active_processes=(1234,),
        patch_equivalent_in_hq=True,
    )
    source = assess_disposable_worktree_cleanup(
        r"C:\NWR\disposable",
        registered=True,
        changed_paths=("src/unique_owner_change.py",),
        patch_equivalent_in_hq=True,
    )
    assert not active.safe and not source.safe


def test_cleanup_allows_only_known_generated_side_effect_signature() -> None:
    result = assess_disposable_worktree_cleanup(
        r"C:\NWR\disposable",
        registered=True,
        changed_paths=tuple(sorted(KNOWN_GENERATED_PATHS - {"uv.lock"})),
        untracked_paths=("uv.lock",),
        patch_equivalent_in_hq=True,
    )
    assert result.safe and result.verdict == "SAFE_DISPOSABLE_WORKTREE_REMOVAL_AUTHORIZED"
