from __future__ import annotations

import hashlib
import hmac
import json
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from typing import Any
from urllib.parse import quote

import pytest

from src.application.desktop_facade import FacadePayload
from src.desktop_api.server import (
    BODY_LIMIT_BYTES,
    STARTUP_CHALLENGE_HEADER,
    STARTUP_PROTOCOL,
    DesktopApiServer,
    create_desktop_api_server,
    validate_bind_host,
    validate_token,
)

TOKEN = "nwr-desktop-test-0123456789-ABCDEF-abcdef"
PROOF_KEY = "nwr-startup-proof-9876543210-FEDCBA-fedcba"


class FakeFacade:
    def __init__(self, mode: str, *, crash: bool = False) -> None:
        self.mode = mode
        self.crash = crash
        self.calls: list[tuple[str, Any]] = []
        self.active_profile_id = "profile-1"

    def bootstrap(self) -> FacadePayload:
        if self.crash:
            raise RuntimeError("failed at C:\\private\\governed.csv")
        return FacadePayload(
            data={
                "ready": True,
                "source_path": Path("C:/private/governed.csv"),
                "nested": {"sourcePath": "C:\\private\\governed.csv"},
            }
        )

    def dynasty_asset(self, asset_id: str) -> FacadePayload:
        self.calls.append(("asset", asset_id))
        return FacadePayload(data={"assetId": asset_id})

    def compare_dynasty_assets(self, asset_ids: list[str]) -> FacadePayload:
        self.calls.append(("compare", asset_ids))
        return FacadePayload(data={"assetIds": asset_ids})

    def evaluate_dynasty_trade(
        self,
        *,
        give: list[str],
        receive: list[str],
        team_window: str,
    ) -> FacadePayload:
        value = {"give": give, "receive": receive, "teamWindow": team_window}
        self.calls.append(("trade", value))
        return FacadePayload(data=value)

    def list_dynasty_trades(self) -> FacadePayload:
        self.calls.append(("trade-list", None))
        return FacadePayload(
            data={"storeStatus": "loaded", "updatedAtUtc": "", "message": "", "scenarios": []}
        )

    def dynasty_workspace(self) -> FacadePayload:
        self.calls.append(("workspace", None))
        return FacadePayload(
            data={
                "storeStatus": "loaded",
                "personalBoard": [],
                "decisions": [],
                "backup": {"status": "none"},
            }
        )

    def save_dynasty_personal_entry(self, **value: Any) -> FacadePayload:
        self.calls.append(("personal-board", value))
        return self.dynasty_workspace()

    def create_dynasty_decision(self, **value: Any) -> FacadePayload:
        self.calls.append(("decision-create", value))
        return self.dynasty_workspace()

    def backup_dynasty_workspace(self) -> FacadePayload:
        self.calls.append(("workspace-backup", None))
        return self.dynasty_workspace()

    def check_dynasty_workspace_restore(self) -> FacadePayload:
        self.calls.append(("workspace-check", None))
        return self.dynasty_workspace()

    def adopt_legacy_dynasty_workspace(self, *, confirmed: bool) -> FacadePayload:
        self.calls.append(("workspace-adopt", confirmed))
        return self.dynasty_workspace()

    def save_dynasty_trade(
        self,
        *,
        scenario_id: str | None,
        title: str,
        give: list[str],
        receive: list[str],
        team_window: str,
        notes: str,
    ) -> FacadePayload:
        value = {
            "scenarioId": scenario_id,
            "title": title,
            "give": give,
            "receive": receive,
            "teamWindow": team_window,
            "notes": notes,
        }
        self.calls.append(("trade-save", value))
        return FacadePayload(data={"scenarioId": scenario_id or "desktop-trade:new"})

    def export_dynasty_trade(
        self,
        *,
        title: str,
        give: list[str],
        receive: list[str],
        team_window: str,
        notes: str,
    ) -> FacadePayload:
        value = {
            "title": title,
            "give": give,
            "receive": receive,
            "teamWindow": team_window,
            "notes": notes,
        }
        self.calls.append(("trade-export", value))
        return FacadePayload(data={"fileName": "nwr-trade-brief.md", "markdown": "# Brief"})

    def save_dynasty_planning_module(
        self,
        *,
        module_id: str,
        checks: list[bool],
        notes: str,
    ) -> FacadePayload:
        value = {"moduleId": module_id, "checks": checks, "notes": notes}
        self.calls.append(("planning", value))
        return FacadePayload(data={"storeStatus": "loaded", "modules": [value]})

    def create_redraft_profile(self, *, preset_key: str, league_name: str | None) -> FacadePayload:
        value = {"presetKey": preset_key, "leagueName": league_name}
        self.calls.append(("create", value))
        return FacadePayload(data={"profile": {"profileId": "created-profile"}})

    def redraft_bootstrap(self) -> FacadePayload:
        return FacadePayload(
            data={
                "profiles": [],
                "presets": [],
                "activeProfileId": self.active_profile_id,
                "rankings": [],
                "draftBoard": {
                    "schema_version": 1,
                    "profile_id": "profile-1",
                    "drafted": ["fixture-player"],
                },
                "health": {"status": "BLOCKED_CURRENT_SEASON_EVIDENCE"},
            }
        )

    def activate_redraft_profile(self, profile_id: str) -> FacadePayload:
        self.active_profile_id = profile_id
        self.calls.append(("activate", profile_id))
        return FacadePayload(data={"profileId": profile_id})

    def duplicate_redraft_profile(
        self,
        profile_id: str,
        *,
        league_name: str | None = None,
    ) -> FacadePayload:
        value = {"profileId": profile_id, "leagueName": league_name}
        self.calls.append(("duplicate", value))
        self.active_profile_id = "duplicated-profile"
        return FacadePayload(data={"profile": {"profileId": "duplicated-profile"}})

    def update_redraft_profile(
        self,
        profile_id: str,
        **settings: Any,
    ) -> FacadePayload:
        value = {"profileId": profile_id, **settings}
        self.calls.append(("edit", value))
        return FacadePayload(data={"profile": {"profileId": profile_id}})

    def mark_redraft_player(
        self,
        *,
        profile_id: str,
        player_id: str,
        drafted: bool,
    ) -> FacadePayload:
        value = {"profileId": profile_id, "playerId": player_id, "drafted": drafted}
        self.calls.append(("mark", value))
        return FacadePayload(data=value)

    def undo_redraft_pick(self, *, profile_id: str) -> FacadePayload:
        self.calls.append(("undo", profile_id))
        return FacadePayload(data={"profileId": profile_id})

    def start_redraft_draft_room(self, **value: Any) -> FacadePayload:
        self.calls.append(("draft-start", value))
        return FacadePayload(data=value)

    def advance_redraft_draft_room(self, **value: Any) -> FacadePayload:
        self.calls.append(("draft-advance", value))
        return FacadePayload(data=value)

    def import_redraft_adp(self, **value: Any) -> FacadePayload:
        self.calls.append(("adp-import", value))
        return FacadePayload(data=value)

    def refresh_redraft_adp(self, **value: Any) -> FacadePayload:
        self.calls.append(("adp-refresh", value))
        return FacadePayload(data=value)

    def ingest_redraft_sleeper_pick(self, **value: Any) -> FacadePayload:
        self.calls.append(("sleeper-pick", value))
        return FacadePayload(data=value)


@contextmanager
def running_server(facade: FakeFacade) -> Iterator[DesktopApiServer]:
    server = create_desktop_api_server(
        host="127.0.0.1",
        port=0,
        token=TOKEN,
        startup_proof_key=PROOF_KEY,
        facade=facade,  # type: ignore[arg-type]
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def request(
    server: DesktopApiServer,
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, str], dict[str, Any] | None]:
    request_headers = dict(headers or {})
    encoded: bytes | None = None
    if body is not None:
        encoded = json.dumps(body).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
    connection.request(method, path, body=encoded, headers=request_headers)
    response = connection.getresponse()
    payload_bytes = response.read()
    response_headers = {key.lower(): value for key, value in response.getheaders()}
    connection.close()
    payload = json.loads(payload_bytes) if payload_bytes else None
    return response.status, response_headers, payload


def authenticated_headers(*, origin: str | None = None) -> dict[str, str]:
    headers = {"X-NWR-Desktop-Token": TOKEN}
    if origin is not None:
        headers["Origin"] = origin
    return headers


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.50", "localhost", ""])
def test_server_rejects_non_explicit_loopback_hosts(host: str) -> None:
    with pytest.raises(ValueError):
        validate_bind_host(host)


@pytest.mark.parametrize(
    "token",
    ["", "short", "a" * 64, "changeMe-changeMe-changeMe-changeMe-12345678"],
)
def test_server_rejects_missing_or_weak_tokens(token: str) -> None:
    with pytest.raises(ValueError):
        validate_token(token)


def test_health_requires_token_and_emits_no_store_contract() -> None:
    with running_server(FakeFacade("dynasty")) as server:
        unauthenticated = request(server, "GET", "/healthz")
        wrong = request(
            server,
            "GET",
            "/healthz",
            headers={"X-NWR-Desktop-Token": TOKEN + "wrong"},
        )
        status, headers, payload = request(
            server,
            "GET",
            "/healthz",
            headers=authenticated_headers(),
        )

    assert unauthenticated[0] == 401
    assert wrong[0] == 403
    assert status == 200
    assert headers["cache-control"] == "no-store, max-age=0"
    assert headers["x-content-type-options"] == "nosniff"
    assert payload is not None
    assert set(payload) == {"contractVersion", "mode", "data", "warnings", "errors"}
    assert payload["contractVersion"] == "1.0.0"
    assert payload["mode"] == "dynasty"


def test_cors_is_an_exact_mode_scoped_allowlist() -> None:
    dynasty_dev = "http://127.0.0.1:1421"
    redraft_dev = "http://127.0.0.1:1422"
    with running_server(FakeFacade("dynasty")) as server:
        exact = request(
            server,
            "GET",
            "/healthz",
            headers=authenticated_headers(origin=dynasty_dev),
        )
        production = request(
            server,
            "GET",
            "/healthz",
            headers=authenticated_headers(origin="http://tauri.localhost"),
        )
        wrong_mode = request(
            server,
            "GET",
            "/healthz",
            headers=authenticated_headers(origin=redraft_dev),
        )
        lookalike = request(
            server,
            "GET",
            "/healthz",
            headers=authenticated_headers(origin=f"{dynasty_dev}.evil.example"),
        )
        preflight = request(
            server,
            "OPTIONS",
            "/api/v1/bootstrap",
            headers={"Origin": dynasty_dev},
        )

    assert exact[0] == production[0] == 200
    assert exact[1]["access-control-allow-origin"] == dynasty_dev
    assert production[1]["access-control-allow-origin"] == "http://tauri.localhost"
    assert wrong_mode[0] == lookalike[0] == 403
    assert "access-control-allow-origin" not in wrong_mode[1]
    assert preflight[0] == 204
    assert preflight[1]["access-control-allow-origin"] == dynasty_dev


def test_mode_isolation_returns_not_found_contract() -> None:
    with running_server(FakeFacade("redraft")) as server:
        status, _, payload = request(
            server,
            "GET",
            "/api/v1/dynasty/assets/current%3Afixture-player",
            headers=authenticated_headers(),
        )

    assert status == 404
    assert payload is not None
    assert payload["mode"] == "redraft"
    assert payload["errors"][0]["code"] == "MODE_ROUTE_UNAVAILABLE"


def test_dynasty_routes_decode_ids_and_accept_canonical_receive_key() -> None:
    facade = FakeFacade("dynasty")
    asset_id = "current:fixture-player"
    with running_server(facade) as server:
        asset = request(
            server,
            "GET",
            f"/api/v1/dynasty/assets/{quote(asset_id, safe='')}",
            headers=authenticated_headers(),
        )
        compare = request(
            server,
            "POST",
            "/api/v1/dynasty/compare",
            body={"assetIds": [asset_id, "current:second"]},
            headers=authenticated_headers(),
        )
        trade = request(
            server,
            "POST",
            "/api/v1/dynasty/trades/evaluate",
            body={"give": [asset_id], "receive": ["pick:2027:1"], "teamWindow": "Balanced"},
            headers=authenticated_headers(),
        )

    assert asset[0] == compare[0] == trade[0] == 200
    assert ("asset", asset_id) in facade.calls
    assert ("compare", [asset_id, "current:second"]) in facade.calls
    assert (
        "trade",
        {"give": [asset_id], "receive": ["pick:2027:1"], "teamWindow": "Balanced"},
    ) in facade.calls


def test_dynasty_saved_trade_routes_are_typed_and_scoped() -> None:
    facade = FakeFacade("dynasty")
    trade = {
        "scenarioId": None,
        "title": "Contender window",
        "give": ["current:fixture-player"],
        "receive": ["pick:2027:1"],
        "teamWindow": "Contending",
        "notes": "Exact governed sides.",
    }
    with running_server(facade) as server:
        listed = request(
            server,
            "GET",
            "/api/v1/dynasty/trades",
            headers=authenticated_headers(),
        )
        saved = request(
            server,
            "POST",
            "/api/v1/dynasty/trades",
            body=trade,
            headers=authenticated_headers(),
        )
        exported = request(
            server,
            "POST",
            "/api/v1/dynasty/trades/export",
            body={key: value for key, value in trade.items() if key != "scenarioId"},
            headers=authenticated_headers(),
        )
        invalid = request(
            server,
            "POST",
            "/api/v1/dynasty/trades",
            body={**trade, "combinedScore": 99},
            headers=authenticated_headers(),
        )

    assert listed[0] == saved[0] == exported[0] == 200
    assert saved[2]["data"]["scenarioId"] == "desktop-trade:new"
    assert exported[2]["data"]["fileName"] == "nwr-trade-brief.md"
    assert ("trade-list", None) in facade.calls
    assert ("trade-save", trade) in facade.calls
    assert (
        "trade-export",
        {key: value for key, value in trade.items() if key != "scenarioId"},
    ) in facade.calls
    assert invalid[0] == 400
    assert invalid[2]["errors"][0]["code"] == "INVALID_REQUEST_BODY"
    assert sum(call[0] == "trade-save" for call in facade.calls) == 1


def test_dynasty_planning_route_is_authenticated_typed_and_scoped() -> None:
    facade = FakeFacade("dynasty")
    with running_server(facade) as server:
        saved = request(
            server,
            "POST",
            "/api/v1/dynasty/planning/modules/draft",
            body={"checks": [True, False, True, False], "notes": "Verify the pick ledger."},
            headers=authenticated_headers(),
        )
        invalid_type = request(
            server,
            "POST",
            "/api/v1/dynasty/planning/modules/draft",
            body={"checks": "not-an-array", "notes": "blocked"},
            headers=authenticated_headers(),
        )
        unknown_field = request(
            server,
            "POST",
            "/api/v1/dynasty/planning/modules/draft",
            body={"checks": [False] * 4, "notes": "blocked", "rank": 1},
            headers=authenticated_headers(),
        )

    assert saved[0] == 200
    assert saved[2]["data"]["storeStatus"] == "loaded"
    assert (
        "planning",
        {
            "moduleId": "draft",
            "checks": [True, False, True, False],
            "notes": "Verify the pick ledger.",
        },
    ) in facade.calls
    assert invalid_type[0] == unknown_field[0] == 400
    assert invalid_type[2]["errors"][0]["code"] == "INVALID_REQUEST_BODY"
    assert unknown_field[2]["errors"][0]["code"] == "INVALID_REQUEST_BODY"
    assert sum(call[0] == "planning" for call in facade.calls) == 1


def test_bootstrap_serialization_never_exposes_paths_or_nan() -> None:
    with running_server(FakeFacade("dynasty")) as server:
        status, _, payload = request(
            server,
            "GET",
            "/api/v1/bootstrap",
            headers=authenticated_headers(),
        )

    encoded = json.dumps(payload, allow_nan=False)
    assert status == 200
    assert "sourcePath" not in payload["data"]
    assert "sourcePath" not in payload["data"]["nested"]
    assert "C:\\" not in encoded


def test_dynasty_workspace_routes_are_bounded_and_authenticated() -> None:
    facade = FakeFacade("dynasty")
    board_body = {
        "assetId": "current:1",
        "watchlist": True,
        "target": False,
        "avoid": False,
        "tags": ["camp"],
        "notes": "Revisit after camp.",
        "teamWindow": "Contending",
    }
    decision_body = {
        "title": "Camp checkpoint",
        "decisionType": "player evaluation",
        "assetIds": ["current:1"],
        "rationale": "Role security needs another check.",
    }
    with running_server(facade) as server:
        loaded = request(
            server,
            "GET",
            "/api/v1/dynasty/workspace",
            headers=authenticated_headers(),
        )
        board = request(
            server,
            "POST",
            "/api/v1/dynasty/workspace/personal-board",
            body=board_body,
            headers=authenticated_headers(),
        )
        decision = request(
            server,
            "POST",
            "/api/v1/dynasty/workspace/decisions",
            body=decision_body,
            headers=authenticated_headers(),
        )
        backup = request(
            server,
            "POST",
            "/api/v1/dynasty/workspace/backup",
            body={},
            headers=authenticated_headers(),
        )
        checked = request(
            server,
            "POST",
            "/api/v1/dynasty/workspace/backup/check",
            body={},
            headers=authenticated_headers(),
        )
        adopted = request(
            server,
            "POST",
            "/api/v1/dynasty/workspace/adopt-legacy",
            body={"confirmed": True},
            headers=authenticated_headers(),
        )
        invalid_adoption = request(
            server,
            "POST",
            "/api/v1/dynasty/workspace/adopt-legacy",
            body={"confirmed": 1},
            headers=authenticated_headers(),
        )
        invalid = request(
            server,
            "POST",
            "/api/v1/dynasty/workspace/personal-board",
            body={**board_body, "watchlist": 1},
            headers=authenticated_headers(),
        )
        unauthenticated = request(server, "GET", "/api/v1/dynasty/workspace")

    assert loaded[0] == board[0] == decision[0] == backup[0] == checked[0] == adopted[0] == 200
    assert invalid[0] == 400
    assert invalid_adoption[0] == 400
    assert unauthenticated[0] == 401
    assert (
        "personal-board",
        {
            "asset_id": "current:1",
            "watchlist": True,
            "target": False,
            "avoid": False,
            "tags": ["camp"],
            "notes": "Revisit after camp.",
            "team_window": "Contending",
        },
    ) in facade.calls
    assert any(call[0] == "decision-create" for call in facade.calls)
    assert ("workspace-adopt", True) in facade.calls
    assert sum(call[0] == "personal-board" for call in facade.calls) == 1


def test_redraft_mutation_routes_return_bootstrap_and_reject_pick_metadata() -> None:
    facade = FakeFacade("redraft")
    with running_server(facade) as server:
        created = request(
            server,
            "POST",
            "/api/v1/redraft/profiles",
            body={"presetKey": "12_TEAM_PPR", "leagueName": "Fixture"},
            headers=authenticated_headers(),
        )
        activated = request(
            server,
            "POST",
            "/api/v1/redraft/profiles/profile-1/activate",
            body={},
            headers=authenticated_headers(),
        )
        marked = request(
            server,
            "POST",
            "/api/v1/redraft/draft/profile-1/pick",
            body={"playerId": "fixture-player"},
            headers=authenticated_headers(),
        )
        rejected = request(
            server,
            "POST",
            "/api/v1/redraft/draft/profile-1/pick",
            body={"playerId": "fixture-player", "pickNumber": 1, "draftedBy": "Me"},
            headers=authenticated_headers(),
        )
        undone = request(
            server,
            "POST",
            "/api/v1/redraft/draft/profile-1/undo",
            body={},
            headers=authenticated_headers(),
        )

    assert created[0] == activated[0] == marked[0] == undone[0] == 200
    assert created[2]["data"]["activeProfileId"] == "created-profile"
    assert facade.calls[:2] == [
        ("create", {"presetKey": "12_TEAM_PPR", "leagueName": "Fixture"}),
        ("activate", "created-profile"),
    ]
    assert rejected[0] == 400
    assert marked[2]["data"]["draftBoard"] == {
        "schemaVersion": 1,
        "profileId": "profile-1",
        "drafted": ["fixture-player"],
    }
    assert rejected[2]["errors"][0]["code"] == "INVALID_REQUEST_BODY"
    assert (
        "mark",
        {"profileId": "profile-1", "playerId": "fixture-player", "drafted": True},
    ) in facade.calls
    assert (
        facade.calls.count(
            ("mark", {"profileId": "profile-1", "playerId": "fixture-player", "drafted": True})
        )
        == 1
    )
    assert ("undo", "profile-1") in facade.calls


def test_draft_room_adp_and_read_only_sleeper_routes_are_strict() -> None:
    facade = FakeFacade("redraft")
    with running_server(facade) as server:
        start = request(
            server,
            "POST",
            "/api/v1/redraft/draft/profile-1/start",
            body={"ownerSlot": 9, "seed": 20260817, "speed": "NORMAL", "mode": "MOCK"},
            headers=authenticated_headers(),
        )
        advance = request(
            server,
            "POST",
            "/api/v1/redraft/draft/profile-1/advance",
            body={"onePick": False},
            headers=authenticated_headers(),
        )
        adp = request(
            server,
            "POST",
            "/api/v1/redraft/adp/profile-1/import",
            body={"csvText": "player,position,overall_adp,source,scoring_format,team_count,date\n"},
            headers=authenticated_headers(),
        )
        refreshed = request(
            server,
            "POST",
            "/api/v1/redraft/adp/profile-1/refresh",
            body={},
            headers=authenticated_headers(),
        )
        sleeper = request(
            server,
            "POST",
            "/api/v1/redraft/draft/profile-1/sleeper-pick",
            body={"playerId": "fixture-player", "pickNumber": 1},
            headers=authenticated_headers(),
        )
        invalid = request(
            server,
            "POST",
            "/api/v1/redraft/draft/profile-1/start",
            body={"ownerSlot": True, "seed": 1, "speed": "FAST", "mode": "MOCK"},
            headers=authenticated_headers(),
        )

    assert start[0] == advance[0] == adp[0] == refreshed[0] == sleeper[0] == 200
    assert invalid[0] == 400
    assert (
        "draft-start",
        {
            "profile_id": "profile-1",
            "owner_slot": 9,
            "seed": 20260817,
            "speed": "NORMAL",
            "mode": "MOCK",
        },
    ) in facade.calls
    assert ("draft-advance", {"profile_id": "profile-1", "one_pick": False}) in facade.calls
    assert any(call[0] == "adp-import" for call in facade.calls)
    assert ("adp-refresh", {"profile_id": "profile-1"}) in facade.calls
    assert (
        "sleeper-pick",
        {"profile_id": "profile-1", "player_id": "fixture-player", "pick_number": 1},
    ) in facade.calls


def test_redraft_profile_duplicate_and_edit_routes_are_strict() -> None:
    facade = FakeFacade("redraft")
    edit = {
        "leagueName": "Sunday League",
        "teamCount": 10,
        "roster": {
            "qb": 1,
            "rb": 2,
            "wr": 3,
            "te": 1,
            "flex": 1,
            "superflex": 0,
            "k": 0,
            "dst": 0,
            "benchSize": 7,
        },
        "scoring": {
            "reception": 1.0,
            "passingTd": 4.0,
            "interception": -2.0,
            "tePremium": 0.5,
        },
        "draft": {
            "rounds": 16,
            "draftSlot": 4,
            "replacementMethod": "expected_available",
        },
    }
    with running_server(facade) as server:
        duplicated = request(
            server,
            "POST",
            "/api/v1/redraft/profiles/profile-1/duplicate",
            body={"leagueName": "Sunday League Copy"},
            headers=authenticated_headers(),
        )
        updated = request(
            server,
            "POST",
            "/api/v1/redraft/profiles/profile-1/edit",
            body=edit,
            headers=authenticated_headers(),
        )
        unknown = request(
            server,
            "POST",
            "/api/v1/redraft/profiles/profile-1/edit",
            body={**edit, "dynastyMode": True},
            headers=authenticated_headers(),
        )
        invalid_nested = request(
            server,
            "POST",
            "/api/v1/redraft/profiles/profile-1/edit",
            body={**edit, "roster": {**edit["roster"], "qb": True}},
            headers=authenticated_headers(),
        )

    assert duplicated[0] == updated[0] == 200
    assert duplicated[2]["data"]["activeProfileId"] == "duplicated-profile"
    assert (
        "duplicate",
        {"profileId": "profile-1", "leagueName": "Sunday League Copy"},
    ) in facade.calls
    assert any(call[0] == "edit" and call[1]["team_count"] == 10 for call in facade.calls)
    assert unknown[0] == invalid_nested[0] == 400
    assert unknown[2]["errors"][0]["code"] == "INVALID_REQUEST_BODY"
    assert invalid_nested[2]["errors"][0]["code"] == "INVALID_REQUEST_BODY"
    assert sum(call[0] == "edit" for call in facade.calls) == 1


def test_internal_errors_are_sanitized() -> None:
    with running_server(FakeFacade("dynasty", crash=True)) as server:
        status, _, payload = request(
            server,
            "GET",
            "/api/v1/bootstrap",
            headers=authenticated_headers(),
        )

    encoded = json.dumps(payload)
    assert status == 500
    assert set(payload) == {"contractVersion", "mode", "data", "warnings", "errors"}
    assert "code" not in payload
    assert "message" not in payload
    assert payload["errors"] == [
        {
            "code": "INTERNAL_ERROR",
            "message": "The local desktop service could not complete the request.",
        }
    ]
    assert "private" not in encoded.casefold()
    assert "C:\\" not in encoded


def test_oversized_json_body_is_rejected_before_reading() -> None:
    facade = FakeFacade("dynasty")
    with running_server(facade) as server:
        status, _, payload = request(
            server,
            "POST",
            "/api/v1/dynasty/compare",
            headers={
                **authenticated_headers(),
                "Content-Type": "application/json",
                "Content-Length": str(BODY_LIMIT_BYTES + 1),
            },
        )

    assert status == 413
    assert payload["errors"][0]["code"] == "REQUEST_BODY_TOO_LARGE"
    assert facade.calls == []


def test_disallowed_methods_still_require_authentication() -> None:
    with running_server(FakeFacade("dynasty")) as server:
        unauthenticated = request(server, "DELETE", "/api/v1/bootstrap")
        authenticated = request(
            server,
            "DELETE",
            "/api/v1/bootstrap",
            headers=authenticated_headers(),
        )

    assert unauthenticated[0] == 401
    assert authenticated[0] == 405


def test_random_port_is_atomically_bound_in_the_ephemeral_high_range() -> None:
    with running_server(FakeFacade("dynasty")) as server:
        assert 49152 <= server.server_port <= 65535


def test_startup_proof_binds_protocol_mode_port_and_fresh_challenge() -> None:
    challenge = "0123456789abcdef" * 4
    with running_server(FakeFacade("dynasty")) as server:
        status, headers, payload = request(
            server,
            "GET",
            "/startup-proof",
            headers={STARTUP_CHALLENGE_HEADER: challenge},
        )
        port = server.server_port

    message = f"{STARTUP_PROTOCOL}\ndynasty\n{port}\n{challenge}".encode("ascii")
    expected = hmac.new(PROOF_KEY.encode("ascii"), message, hashlib.sha256).hexdigest()
    assert status == 200
    assert headers["cache-control"] == "no-store, max-age=0"
    assert payload is not None
    assert payload["contractVersion"] == "1.0.0"
    assert payload["mode"] == "dynasty"
    assert payload["data"] == {
        "status": "starting",
        "transport": "loopback",
        "startupProof": expected,
    }


@pytest.mark.parametrize(
    "challenge",
    ["", "abc", "A" * 64, "g" * 64, "0" * 63, "0" * 65],
)
def test_startup_proof_rejects_noncanonical_challenges(challenge: str) -> None:
    with running_server(FakeFacade("dynasty")) as server:
        status, _, payload = request(
            server,
            "GET",
            "/startup-proof",
            headers={STARTUP_CHALLENGE_HEADER: challenge},
        )

    assert status == 400
    assert payload is not None
    assert payload["errors"][0]["code"] == "INVALID_STARTUP_CHALLENGE"


def test_startup_proof_is_unavailable_to_browser_origins() -> None:
    with running_server(FakeFacade("dynasty")) as server:
        status, _, payload = request(
            server,
            "GET",
            "/startup-proof",
            headers={
                STARTUP_CHALLENGE_HEADER: "0123456789abcdef" * 4,
                "Origin": "http://tauri.localhost",
            },
        )

    assert status == 403
    assert payload is not None
    assert payload["errors"][0]["code"] == "STARTUP_PROOF_ORIGIN_FORBIDDEN"
    assert "startupProof" not in json.dumps(payload)
