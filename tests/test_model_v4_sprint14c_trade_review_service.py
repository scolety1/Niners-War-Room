from __future__ import annotations

import csv
import zipfile
from pathlib import Path

from src.services.model_v4_sprint14c_trade_review_service import (
    EXTERNAL_ASSET_HEADER,
    SUMMARY_HEADER,
    TRADE_AWAY_HEADER,
    build_trade_review_outputs,
    write_trade_review_outputs,
)


def test_14c_builds_review_only_trade_surfaces() -> None:
    result = build_trade_review_outputs()

    assert result.summary["review_status"] == "review_only"
    assert result.summary["trade_away_rows"] == 24
    assert result.summary["external_asset_rows"] == 35
    assert result.summary["trade_recommendations_created"] is False
    assert result.summary["trade_packages_created"] is False
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False


def test_14c_trade_away_rows_are_not_sell_calls() -> None:
    result = build_trade_review_outputs()
    by_name = {row["player_name"]: row for row in result.trade_away_rows}
    disclosure_fields = {"source_path", "source_column", "lineage_class"}

    assert disclosure_fields <= set(TRADE_AWAY_HEADER)
    assert all(disclosure_fields <= set(row) for row in result.trade_away_rows)
    assert {row["source_column"] for row in result.trade_away_rows} == {"pressure_score"}
    assert by_name["Kaleb Johnson"]["trade_away_review_band"] == (
        "liquidity_check_context_review"
    )
    assert by_name["De'Von Achane"]["trade_away_review_band"] == (
        "hold_core_unless_overpay_review"
    )
    assert {row["blocked_use"] for row in result.trade_away_rows} == {
        "do_not_use_as_trade_offer_or_sell_call"
    }


def test_14c_external_asset_rows_exclude_niners_and_remain_review_only() -> None:
    result = build_trade_review_outputs()
    external_names = {row["asset_name"] for row in result.external_asset_rows}
    disclosure_fields = {"source_path", "source_column", "lineage_class"}

    assert "Puka Nacua" in external_names
    assert "Jaxon Smith-Njigba" in external_names
    assert "De'Von Achane" not in external_names
    assert disclosure_fields <= set(EXTERNAL_ASSET_HEADER)
    assert all(disclosure_fields <= set(row) for row in result.external_asset_rows)
    assert {row["source_column"] for row in result.external_asset_rows} == {
        "dynasty_asset_value_review_score"
    }
    assert {row["allowed_use"] for row in result.external_asset_rows} == {
        "review_only_external_asset_context_not_recommendation"
    }
    assert {row["blocked_use"] for row in result.external_asset_rows} == {
        "do_not_use_as_trade_offer_buy_call_or_acquisition_call"
    }
    assert all("external_asset_review_key" in row for row in result.external_asset_rows)
    assert all("external_asset_review_band" in row for row in result.external_asset_rows)


def test_14c_external_asset_rows_have_no_trade_for_or_target_framing() -> None:
    result = build_trade_review_outputs()
    banned_terms = ("trade_for", "trade-for", "target")

    for row in result.external_asset_rows:
        text = " ".join(
            str(row[field]).lower()
            for field in (
                "external_asset_review_key",
                "external_asset_review_band",
                "review_rationale",
                "allowed_use",
                "blocked_use",
            )
        )
        assert not any(term in text for term in banned_terms)


def test_14c_components_and_warnings_are_visible() -> None:
    result = build_trade_review_outputs()

    assert len(result.component_rows) == (24 * 3) + (35 * 3)
    assert len(result.receipt_rows) == 24 + 35
    warning_codes = {row["warning_code"] for row in result.warning_rows}
    assert "no_trade_offers_or_recommendations_created" in warning_codes
    assert "trade_away_context_not_sell_recommendation" in warning_codes
    assert "external_asset_context_not_acquisition_recommendation" in warning_codes


def test_14c_writes_outputs_docs_and_packet(tmp_path: Path) -> None:
    result = build_trade_review_outputs()
    paths = write_trade_review_outputs(
        output_root=tmp_path / "external_asset_reviews",
        packet_root=tmp_path / "packets",
        result=result,
    )

    assert _header(paths.trade_away_rows) == TRADE_AWAY_HEADER
    assert paths.external_asset_rows.name == "external_asset_context_review_rows.csv"
    assert _header(paths.external_asset_rows) == EXTERNAL_ASSET_HEADER
    assert _header(paths.summary) == SUMMARY_HEADER
    assert "External Asset Reviews" in paths.doc.read_text(encoding="utf-8")
    assert paths.audit_packet.exists()
    with zipfile.ZipFile(paths.audit_packet) as archive:
        assert "docs/model_v4/SPRINT_14C_EXTERNAL_AUDIT_PROMPT.md" in archive.namelist()


def _header(path: Path) -> tuple[str, ...]:
    with path.open(newline="", encoding="utf-8") as handle:
        return tuple(next(csv.reader(handle)))
