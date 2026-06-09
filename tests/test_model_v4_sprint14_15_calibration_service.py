from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from src.services.model_v4_sprint14_15_calibration_service import (
    CALIBRATION_SUMMARY_HEADER,
    CONTRACT_HEADER,
    FIXTURE_HEADER,
    NINERS_SANITY_HEADER,
    ROSTER_HEADER,
    build_sprint14_15_review_outputs,
    write_sprint14_15_review_outputs,
)


def test_sprint14a_builds_niners_roster_contract_without_recommendations() -> None:
    result = build_sprint14_15_review_outputs()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["niners_roster_rows"] == 24
    assert result.summary["niners_current_pick_rows"] == 5
    assert result.summary["final_recommendations_created"] is False
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert {row["allowed_use"] for row in result.roster_rows} == {
        "review_only_roster_contract_not_cut_keep_recommendation"
    }


def test_sprint14a_contract_includes_deadline_pressure_and_blocked_outputs() -> None:
    result = build_sprint14_15_review_outputs()
    contract = {row["contract_key"]: row for row in result.contract_rows}

    assert contract["decision_deadline"]["contract_value"] == "June 15"
    assert contract["league_format"]["contract_value"].startswith("10-team 1QB")
    assert contract["blocked_output"]["contract_value"] == (
        "final cut/keep/trade/draft recommendations"
    )
    assert contract["minimum_roster_pressure_count"]["contract_value"] == "1"


def test_sprint15_builds_required_cross_model_fixtures() -> None:
    result = build_sprint14_15_review_outputs()
    groups = {row["fixture_group"] for row in result.fixture_rows}

    assert groups == {
        "aging_veteran_sanity",
        "elite_rb_sanity",
        "elite_wr_sanity",
        "movement_suspicious_ranking_audit",
        "niners_roster_sanity",
        "no_premium_te_sanity",
        "one_qb_qb_sanity",
    }
    by_group = {row["fixture_group"]: row for row in result.fixture_rows}
    assert "Lamar Jackson" in by_group["one_qb_qb_sanity"]["players"]
    assert "Brock Purdy" in by_group["one_qb_qb_sanity"]["players"]
    assert by_group["one_qb_qb_sanity"]["status"] == "pass"
    assert by_group["movement_suspicious_ranking_audit"]["status"] == "review"


def test_sprint15_keeps_suspicious_rows_as_review_only() -> None:
    result = build_sprint14_15_review_outputs()
    review_ids = {row["review_id"] for row in result.suspicious_rows}

    assert "suspicious:te:bowers_kelce" in review_ids
    assert "suspicious:qb:lamar" in review_ids
    assert "suspicious:qb:purdy" in review_ids
    assert {row["severity"] for row in result.suspicious_rows} == {"review"}


def test_sprint15_niners_sanity_rows_cover_roster_players() -> None:
    result = build_sprint14_15_review_outputs()
    names = {row["player_name"] for row in result.niners_sanity_rows}

    assert "Lamar Jackson" in names
    assert "De'Von Achane" in names
    assert "Ricky Pearsall" in names
    assert len(result.niners_sanity_rows) == len(result.roster_rows)


def test_sprint14_15_writes_outputs_docs_and_packet(tmp_path: Path) -> None:
    result = build_sprint14_15_review_outputs()
    paths = write_sprint14_15_review_outputs(
        output_root=tmp_path / "decision_calibration",
        packet_root=tmp_path / "packets",
        result=result,
    )

    assert _header(paths.roster_state) == ROSTER_HEADER
    assert _header(paths.deadline_contract) == CONTRACT_HEADER
    assert _header(paths.calibration_summary) == CALIBRATION_SUMMARY_HEADER
    assert _header(paths.calibration_fixtures) == FIXTURE_HEADER
    assert _header(paths.niners_roster_sanity) == NINERS_SANITY_HEADER
    assert "does not recommend cuts" in paths.sprint14_doc.read_text(encoding="utf-8")
    assert "football sanity fixtures" in paths.sprint15_doc.read_text(encoding="utf-8")
    assert paths.audit_packet.exists()
    with zipfile.ZipFile(paths.audit_packet) as archive:
        assert "docs/model_v4/SPRINT_14A_15_EXTERNAL_AUDIT_PROMPT.md" in archive.namelist()


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
