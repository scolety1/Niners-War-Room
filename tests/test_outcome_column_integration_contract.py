from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/model_v4/OUTCOME_COLUMN_INTEGRATION_CONTRACT_20260610.md"


def test_outcome_column_contract_exists_and_names_landing_zone() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "local_exports/model_v4/outcomes/incoming/<package_id>/" in text
    assert "local_exports/model_v4/outcomes/latest/" in text
    assert "outcome_player_probabilities.csv" in text
    assert "outcome_guardrail_report.csv" in text


def test_outcome_column_contract_requires_expected_probability_schema() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    for column in (
        "top_6_2026_prob",
        "top_12_2026_prob",
        "top_24_2026_prob",
        "top_36_2026_prob",
        "top_48_2026_prob",
        "top_6_2027_prob",
        "top_12_2027_prob",
        "top_24_2027_prob",
        "top_12_next_5y_prob",
        "useful_starter_prob",
        "bust_prob",
        "outcome_confidence",
        "outcome_model_version",
        "outcome_generated_at",
    ):
        assert column in text


def test_outcome_column_contract_blocks_fake_probabilities_and_banned_inputs() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "do not show fake probabilities" in text.lower()
    assert "display `--` or `In development`" in text
    for blocked in (
        "ADP",
        "market",
        "league",
        "public rank",
        "consensus",
        "projection",
        "trade calculator",
        "RotoWire rankings/projections",
        "prior draft history",
        "legacy active-pack `private_score`",
    ):
        assert blocked in text


def test_outcome_column_contract_preserves_current_sentinels() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "2026 5.04 remains no-baseline/manual watchlist/no exact equivalence" in text
    assert "Keenan Allen legacy `82.4` remains comparison-only" in text
    assert "Darius Slayton legacy `78.88` remains comparison-only" in text
