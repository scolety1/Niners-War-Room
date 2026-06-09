import csv
from collections import Counter
from pathlib import Path

from src.services.model_v4_sprint14c_trade_review_service import (
    build_trade_review_outputs,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/model_v4/EXTERNAL_ASSET_REVIEWS_SANITY_AUDIT_20260605.md"
TRADE_PAGE = ROOT / "app/pages/04_trade_central.py"
CANONICAL_EXTERNAL = (
    ROOT
    / "local_exports/model_v4/external_asset_reviews/latest/"
    "external_asset_context_review_rows.csv"
)
CANONICAL_AWAY = (
    ROOT
    / "local_exports/model_v4/external_asset_reviews/latest/"
    "trade_away_candidate_review_rows.csv"
)
FALLBACK_EXTERNAL = (
    ROOT
    / "local_exports/model_v4/trade_review/latest/trade_for_candidate_review_rows.csv"
)


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_external_asset_report_discloses_sources_and_missing_canonical_exports():
    text = REPORT.read_text(encoding="utf-8")

    assert "build_trade_review_outputs()" in text
    assert "external_asset_context_review_rows.csv" in text
    assert "trade_away_candidate_review_rows.csv" in text
    assert "dynasty_asset_value_review_rows.csv" in text
    assert "Canonical External Asset Review CSVs are missing locally" in text
    assert not CANONICAL_EXTERNAL.exists()
    assert not CANONICAL_AWAY.exists()
    assert FALLBACK_EXTERNAL.exists()


def test_external_asset_repaired_service_rows_have_review_only_disclosure():
    result = build_trade_review_outputs()
    external_rows = result.external_asset_rows
    away_rows = result.trade_away_rows

    assert result.summary["review_status"] == "review_only"
    assert result.summary["external_asset_rows"] == 35
    assert result.summary["trade_away_rows"] == 24
    assert result.summary["trade_recommendations_created"] is False
    assert result.summary["trade_packages_created"] is False
    assert result.summary["active_rankings_changed"] is False
    assert result.summary["readiness_unlocked"] is False
    assert {row["source_column"] for row in external_rows} == {
        "dynasty_asset_value_review_score"
    }
    assert {row["lineage_class"] for row in external_rows} == {
        "review_v4_dynasty_asset"
    }
    assert {row["allowed_use"] for row in external_rows} == {
        "review_only_external_asset_context_not_recommendation"
    }
    assert {row["blocked_use"] for row in external_rows} == {
        "do_not_use_as_trade_offer_buy_call_or_acquisition_call"
    }
    assert {row["source_column"] for row in away_rows} == {"pressure_score"}
    assert {row["lineage_class"] for row in away_rows} == {
        "review_v4_roster_pressure_context"
    }


def test_external_asset_report_matches_service_band_counts_and_top_rows():
    text = REPORT.read_text(encoding="utf-8")
    result = build_trade_review_outputs()
    external_rows = result.external_asset_rows
    bands = Counter(row["external_asset_review_band"] for row in external_rows)

    assert bands["elite_external_asset_context_review"] == 7
    assert bands["strong_external_asset_context_review"] == 10
    assert bands["external_asset_context_review"] == 16
    assert bands["roster_fit_external_asset_context_review"] == 2
    for asset in [
        "Trey McBride",
        "Puka Nacua",
        "Jaxon Smith-Njigba",
        "Christian McCaffrey",
        "Josh Allen",
        "Ja'Marr Chase",
    ]:
        assert asset in text


def test_external_asset_repaired_rows_have_no_target_or_trade_for_framing():
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


def test_external_asset_audit_records_fallback_stale_naming_and_ui_framing():
    report = REPORT.read_text(encoding="utf-8")
    page = TRADE_PAGE.read_text(encoding="utf-8")
    fallback_rows = _csv_rows(FALLBACK_EXTERNAL)

    assert "st.title(\"External Asset Reviews\")" in page
    assert "External Asset Context" in page
    assert "review-only" in page
    assert "Trade For Targets" not in page
    assert any(row["trade_for_review_band"] == "elite_target_review" for row in fallback_rows)
    assert "elite_target_review" in report
    assert "compatibility-only evidence" in report
