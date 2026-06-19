from __future__ import annotations

from src.trading_lab.schema_registry import (
    CORE_ARTIFACT_TYPES,
    SCHEMA_REGISTRY,
    prohibited_field_names_in,
    schema_for_artifact,
)
from src.trading_lab.source_inventory import validate_manual_artifact_payload
from tests.test_trading_lab_t7_artifact_validators import VALID_PAYLOADS


def test_t8_schema_registry_includes_core_artifacts() -> None:
    assert set(CORE_ARTIFACT_TYPES) == set(SCHEMA_REGISTRY)


def test_t8_schema_registry_required_fields_are_non_empty_for_manual_artifacts() -> None:
    for artifact_type in VALID_PAYLOADS:
        schema = schema_for_artifact(artifact_type)

        assert schema is not None
        assert schema.required_fields
        assert all(field.strip() for field in schema.required_fields)


def test_t8_schema_registry_lists_prohibited_field_names() -> None:
    fields = ("research_question", "api_key", "token", "notes")

    assert prohibited_field_names_in(fields) == ("api_key", "token")


def test_t8_fake_safe_payloads_remain_accepted() -> None:
    for artifact_type, payload in VALID_PAYLOADS.items():
        assert validate_manual_artifact_payload(artifact_type, payload) == ()
