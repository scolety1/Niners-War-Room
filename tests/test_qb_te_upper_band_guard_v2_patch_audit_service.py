from __future__ import annotations

from pathlib import Path

from src.services.qb_te_upper_band_guard_v2_patch_audit_service import (
    PRE_FULL_HASH,
    build_upper_band_guard_v2_patch_audit,
    write_upper_band_guard_v2_patch_audit,
)


def test_upper_band_guard_v2_patch_audit_acceptance_summary() -> None:
    result = build_upper_band_guard_v2_patch_audit()

    assert len(result.movement_rows) == 240
    assert result.summary["active_output_changed"] is True
    assert result.summary["post_full_hash"] != PRE_FULL_HASH
    assert result.summary["rb_wr_unchanged"] is True
    assert result.summary["sentinels_safe"] is True
    assert result.summary["contamination_safe"] is True
    assert result.summary["failed_acceptance_criteria"] == []
    assert result.summary["verdict"] == "production_patch_ready_for_human_review"


def test_upper_band_guard_v2_patch_audit_shape_checks() -> None:
    rows = build_upper_band_guard_v2_patch_audit().movement_rows
    top25 = [row for row in rows if row["patched_rank"] != "" and row["patched_rank"] <= 25]
    top10 = [row for row in rows if row["patched_rank"] != "" and row["patched_rank"] <= 10]

    assert sum(1 for row in top25 if row["position"] == "QB") <= 3
    assert not any(row["position"] == "QB" for row in top10)
    assert not any(row["position"] == "TE" and row["patched_rank"] == 1 for row in top25)
    assert any(row["position"] == "TE" for row in top25)


def test_upper_band_guard_v2_patch_audit_writes_expected_files(tmp_path: Path) -> None:
    paths = write_upper_band_guard_v2_patch_audit(
        movement_path=tmp_path / "movement.csv",
        audit_path=tmp_path / "audit.md",
        handoff_path=tmp_path / "handoff.md",
    )

    assert paths.movement_audit_csv.exists()
    assert paths.audit_report.exists()
    assert paths.handoff.exists()
    assert "Decision Board remains blocked" in paths.handoff.read_text(encoding="utf-8")
    assert "production_patch_ready_for_human_review" in paths.audit_report.read_text(
        encoding="utf-8"
    )


def test_production_patch_does_not_reference_shadow_or_hardcoded_players() -> None:
    service_text = Path(
        "src/services/model_v4_qb_te_current_value_service.py"
    ).read_text(encoding="utf-8")
    export_text = Path("src/services/full_board_current_value_export_service.py").read_text(
        encoding="utf-8"
    )
    production_text = service_text + "\n" + export_text

    blocked_fragments = (
        "formula_candidates",
        "shadow_rankings",
        "Trey McBride",
        "Brock Bowers",
        "Kyle Pitts",
        "Josh Allen",
        "Darius Slayton",
        "Keenan Allen",
    )
    for fragment in blocked_fragments:
        assert fragment not in production_text


def test_upper_band_guard_v2_uses_private_component_receipts_only() -> None:
    service_text = Path(
        "src/services/model_v4_qb_te_current_value_service.py"
    ).read_text(encoding="utf-8")

    assert "_te_upper_band_guard_gate" in service_text
    assert "route_target_role" in service_text
    assert "first_down_yardage" in service_text
    assert "yprr_target_efficiency" in service_text
    assert "red_zone_secondary" in service_text
    assert "market_rank" not in service_text
    assert "league_rank" not in service_text
    assert "rotowire_projection" not in service_text.lower()
    assert "rotowire_rank" not in service_text.lower()
    assert "rotowire_adp" not in service_text.lower()
    assert "legacy_active_pack" not in service_text
