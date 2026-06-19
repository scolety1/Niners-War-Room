from __future__ import annotations

from dataclasses import dataclass

from src.trading_lab.source_inventory import TRADE_PACKAGE_REQUIRED_FIELDS

FANTASY_TRADE_ARTIFACT_TYPES = frozenset(
    {
        "fantasy_source",
        "trade_package",
        "trade_for_review",
        "trade_away_review",
        "opponent_fit_review",
        "roster_aftermath_review",
    }
)

PROHIBITED_FIELD_NAMES = frozenset(
    {
        "stock_symbol",
        "ticker",
        "broker_account",
        "api_key",
        "secret",
        "token",
        "order_execution",
        "real_money_account",
    }
)


@dataclass(frozen=True)
class ArtifactSchema:
    artifact_type: str
    required_fields: tuple[str, ...]
    purpose: str


SCHEMA_REGISTRY = {
    "trade_package": ArtifactSchema(
        artifact_type="trade_package",
        required_fields=TRADE_PACKAGE_REQUIRED_FIELDS,
        purpose=(
            "Compare NWR value delta, public fantasy fairness, opponent fit, "
            "and roster aftermath."
        ),
    ),
    "fantasy_source": ArtifactSchema(
        artifact_type="fantasy_source",
        required_fields=(
            "source_id",
            "source_name",
            "source_category",
            "allowed_use",
            "prohibited_use",
            "attribution",
        ),
        purpose="Review future fantasy-football source eligibility without ingestion.",
    ),
}


def schema_for_artifact(artifact_type: str) -> ArtifactSchema | None:
    return SCHEMA_REGISTRY.get(artifact_type)


def prohibited_field_names_in(fields: list[str] | tuple[str, ...] | set[str]) -> tuple[str, ...]:
    normalized = {field.lower() for field in fields}
    return tuple(sorted(normalized & PROHIBITED_FIELD_NAMES))
