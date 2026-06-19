from __future__ import annotations

import pytest

from src.trading_lab.source_inventory import (
    ResearchSourceMetadata,
    assert_valid_source_metadata,
    validate_research_config,
    validate_source_metadata,
)


def test_source_metadata_accepts_public_research_source() -> None:
    source = ResearchSourceMetadata(
        source_id="sec_10q_public_filings",
        name="SEC public company filings",
        category="public_company_filings",
        intended_use="education_research",
        access_method="manual public website review",
        attribution="SEC EDGAR public filings, reviewed by URL and filing date",
        reviewed_on="2026-06-18",
        notes="Research-only source for source inventory notes.",
        config={"source_url": "https://www.sec.gov/edgar/search/"},
    )

    assert validate_source_metadata(source) == ()


def test_source_metadata_blocks_prohibited_source_category() -> None:
    source = ResearchSourceMetadata(
        source_id="private_broker_export",
        name="Private brokerage export",
        category="private_brokerage_data",
        intended_use="source_inventory",
        access_method="manual review",
        attribution="Private account export",
    )

    issues = validate_source_metadata(source)

    assert {issue.code for issue in issues} == {"prohibited_source_category"}


def test_source_metadata_blocks_execution_language() -> None:
    source = ResearchSourceMetadata(
        source_id="order_endpoint",
        name="Broker order endpoint",
        category="public_market_data",
        intended_use="education_research",
        access_method="broker API integration",
        attribution="Not allowed",
    )

    issues = validate_source_metadata(source)

    assert "prohibited_execution_language" in {issue.code for issue in issues}


def test_research_config_rejects_secret_like_fields() -> None:
    issues = validate_research_config(
        {
            "source_url": "https://example.test/public",
            "connection": {"api_key": "placeholder"},
        }
    )

    assert any(issue.field == "config.connection.api_key" for issue in issues)
    assert any(issue.code == "secret_like_field" for issue in issues)


def test_assert_valid_source_metadata_raises_with_issue_summary() -> None:
    source = ResearchSourceMetadata(
        source_id="",
        name="Public market data",
        category="public_market_data",
        intended_use="education_research",
        access_method="manual public review",
        attribution="Public source",
    )

    with pytest.raises(ValueError, match="source_id:required"):
        assert_valid_source_metadata(source)
