from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.services import cfbd_official_v2_adapter as cfbd


def test_missing_key_blocks_without_revealing_any_value() -> None:
    status = cfbd.key_status({})
    assert status.present is False
    assert status.status == "BLOCKED_MISSING_OWNER_CONTROLLED_CFBD_KEY"
    with pytest.raises(cfbd.CfbdMissingOwnerKeyError):
        cfbd.token_from_environment({})


def test_key_presence_reports_only_environment_name() -> None:
    status = cfbd.key_status({"CFBD_BEARER_TOKEN": "synthetic-owner-secret"})
    assert status.present is True
    assert status.environment_name == "CFBD_BEARER_TOKEN"
    assert "secret" not in repr(status)


def test_only_authorized_rest_v2_paths_are_constructed() -> None:
    assert cfbd.build_url("/player/usage", {"year": 2024}).endswith(
        "/player/usage?year=2024"
    )
    with pytest.raises(cfbd.CfbdContractError):
        cfbd.build_url("/graphql", {})


def test_request_limit_fails_before_transport() -> None:
    called = False

    def transport(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("transport must not run")

    with pytest.raises(cfbd.CfbdRequestLimitError):
        cfbd.request_json(
            path="/player/search",
            params={},
            transport=transport,
            calls_made=800,
            environ={"CFBD_BEARER_TOKEN": "synthetic"},
        )
    assert called is False


def test_synthetic_fixture_contains_no_credential_material() -> None:
    path = Path(
        "tests/fixtures/new_evidence_foundation_v1/"
        "cfbd_player_season_stats.synthetic.json"
    )
    fixture = json.loads(path.read_text(encoding="utf-8"))
    assert cfbd.synthetic_fixture_is_safe(fixture)
    assert fixture["fixture_class"] == "SYNTHETIC_NOT_PROVIDER_DATA"
