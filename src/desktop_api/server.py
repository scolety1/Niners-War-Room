"""Offline-safe stdlib HTTP server exposing the desktop application facade."""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import re
import secrets
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import unquote, urlsplit

from src.application.contracts import contract_envelope, error_contract
from src.application.desktop_facade import DesktopBackendFacade, FacadeError, FacadePayload

BODY_LIMIT_BYTES = 256 * 1024
MAX_REQUEST_TARGET_BYTES = 4096
MIN_TOKEN_LENGTH = 32
STARTUP_PROTOCOL = "nwr-desktop-startup-v1"
STARTUP_CHALLENGE_HEADER = "X-NWR-Startup-Challenge"
_STARTUP_CHALLENGE = re.compile(r"^[0-9a-f]{64}$")
_HIGH_PORT_MIN = 49152
_HIGH_PORT_ATTEMPTS = 128
_PROFILE_ACTIVATE = re.compile(r"^/api/v1/redraft/profiles/([^/]+)/activate$")
_PROFILE_DUPLICATE = re.compile(r"^/api/v1/redraft/profiles/([^/]+)/duplicate$")
_PROFILE_EDIT = re.compile(r"^/api/v1/redraft/profiles/([^/]+)/edit$")
_SLEEPER_REDRAFT_IMPORT = "/api/v1/redraft/sleeper/import"
_PRACTICAL_MOCK_START = re.compile(r"^/api/v1/redraft/profiles/([^/]+)/practical-mock$")
_REDRAFT_NWR_PURE_MODE = re.compile(r"^/api/v1/redraft/profiles/([^/]+)/nwr-pure-mode$")
_KDST_STREAMER = "/api/v1/redraft/kdst/streamer"
_REDRAFT_DRAFT_PICK = re.compile(r"^/api/v1/redraft/draft/([^/]+)/pick$")
_REDRAFT_DRAFT_UNDO = re.compile(r"^/api/v1/redraft/draft/([^/]+)/undo$")
_REDRAFT_DRAFT_START = re.compile(r"^/api/v1/redraft/draft/([^/]+)/start$")
_REDRAFT_DRAFT_ADVANCE = re.compile(r"^/api/v1/redraft/draft/([^/]+)/advance$")
_REDRAFT_ADP_IMPORT = re.compile(r"^/api/v1/redraft/adp/([^/]+)/import$")
_REDRAFT_ADP_REFRESH = re.compile(r"^/api/v1/redraft/adp/([^/]+)/refresh$")
_REDRAFT_UDK_IMPORT = re.compile(r"^/api/v1/redraft/udk/([^/]+)/import$")
# NWR LAST PRE-DRAFT BLOCKER CLOSURE: the real "all 32 teams' current
# K/DST" UDK snapshot importer, separate from the skill-position rankings
# route above -- previously wired nowhere.
_REDRAFT_UDK_KDST_IMPORT = re.compile(r"^/api/v1/redraft/udk-kdst/([^/]+)/import$")
# NWR NEXT-DRAFT FINAL BLOCKER CLOSURE (section 8): the real UDK
# rollback-one-position facade method (`rollback_udk_position_rankings`)
# and the real status/risk intake contract (`submit_player_status_
# override` / `list_player_status_overrides`) have existed since the
# prior class-time session but were never reachable from any HTTP route.
# Neither needs a local file path -- both take plain JSON fields.
_REDRAFT_UDK_ROLLBACK = re.compile(r"^/api/v1/redraft/udk/([^/]+)/rollback$")
_REDRAFT_STATUS_OVERRIDES = "/api/v1/redraft/status-overrides"
_REDRAFT_PASTE_ADP_PREVIEW = re.compile(r"^/api/v1/redraft/adp/([^/]+)/paste/preview$")
_REDRAFT_PASTE_ADP_SAVE = re.compile(r"^/api/v1/redraft/adp/([^/]+)/paste/save$")
_REDRAFT_PASTE_ADP_ACTIVATE = re.compile(r"^/api/v1/redraft/adp/([^/]+)/paste/activate$")
_REDRAFT_PASTE_ADP_CLEAR = re.compile(r"^/api/v1/redraft/adp/([^/]+)/paste/clear$")
_REDRAFT_PASTE_ADP_SELECTION = re.compile(r"^/api/v1/redraft/adp/([^/]+)/paste/selection$")
_REDRAFT_PASTE_ADP_MANUAL_MATCH = re.compile(r"^/api/v1/redraft/adp/([^/]+)/paste/manual-match$")
_REDRAFT_SLEEPER_PICK = re.compile(r"^/api/v1/redraft/draft/([^/]+)/sleeper-pick$")
_REDRAFT_SLEEPER_SYNC = re.compile(r"^/api/v1/redraft/draft/([^/]+)/sleeper-sync$")
_REDRAFT_PICK_REPLACE = re.compile(r"^/api/v1/redraft/draft/([^/]+)/pick/replace$")
_REDRAFT_PICK_CLEAR = re.compile(r"^/api/v1/redraft/draft/([^/]+)/pick/clear$")
_REDRAFT_PICK_FILL_GAP = re.compile(r"^/api/v1/redraft/draft/([^/]+)/pick/fill-gap$")
_REDRAFT_PICK_CORRECTION_UNDO = re.compile(r"^/api/v1/redraft/draft/([^/]+)/pick/undo-correction$")
_REDRAFT_EXTERNAL_INTELLIGENCE = re.compile(r"^/api/v1/redraft/draft/([^/]+)/external-intelligence$")
_REDRAFT_DECISION_BUNDLE = re.compile(r"^/api/v1/redraft/draft/([^/]+)/decision-bundle$")
_REDRAFT_DECISION_BUNDLE_V2 = re.compile(r"^/api/v1/redraft/draft/([^/]+)/decision-bundle-v2$")
_REDRAFT_CATCH_UP_PREVIEW = re.compile(r"^/api/v1/redraft/draft/([^/]+)/catch-up/preview$")
_REDRAFT_CATCH_UP_APPLY = re.compile(r"^/api/v1/redraft/draft/([^/]+)/catch-up/apply$")
_DYNASTY_PLANNING_MODULE = re.compile(r"^/api/v1/dynasty/planning/modules/([^/]+)$")
_PRODUCTION_DESKTOP_ORIGINS = frozenset(
    {
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    }
)
_MODE_DEV_ORIGINS = {
    "dynasty": "http://127.0.0.1:1421",
    "redraft": "http://127.0.0.1:1422",
}


class RequestContractError(RuntimeError):
    def __init__(self, code: str, message: str, *, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class DesktopApiServer(ThreadingHTTPServer):
    """Threaded loopback server carrying immutable security/runtime configuration."""

    daemon_threads = True
    allow_reuse_address = False

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        facade: DesktopBackendFacade,
        token: str,
        startup_proof_key: str,
    ) -> None:
        self.facade = facade
        self.api_token = token
        self.startup_proof_key = startup_proof_key
        super().__init__(server_address, DesktopApiRequestHandler)
        self.allowed_origins = frozenset(
            (*_PRODUCTION_DESKTOP_ORIGINS, _MODE_DEV_ORIGINS[facade.mode])
        )


class _IPv6DesktopApiServer(DesktopApiServer):
    address_family = socket.AF_INET6


class DesktopApiRequestHandler(BaseHTTPRequestHandler):
    server: DesktopApiServer
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:  # noqa: N802
        self._dispatch("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch("POST")

    def do_OPTIONS(self) -> None:  # noqa: N802
        try:
            self._validate_origin(required=True)
        except RequestContractError as exc:
            self._write_error(exc.status, exc.code, exc.message)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._security_headers(content_length=0)
        self._cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Authorization, Content-Type, X-NWR-Desktop-Token, X-NWR-Token",
        )
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_PUT(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_PATCH(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def do_DELETE(self) -> None:  # noqa: N802
        self._method_not_allowed()

    def log_message(self, format: str, *args: object) -> None:
        """Avoid logging request targets, tokens, or local filesystem details."""

    def _dispatch(self, method: str) -> None:
        try:
            path = self._validated_path()
            if path == "/startup-proof":
                payload = self._startup_proof(method)
            else:
                self._validate_origin(required=False)
                self._authenticate()
                self._enforce_mode_route(path)
                payload = self._route(method, path)
        except RequestContractError as exc:
            self._write_error(exc.status, exc.code, exc.message)
            return
        except FacadeError as exc:
            self._write_error(exc.status, exc.code, exc.message)
            return
        except Exception:
            self._write_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "INTERNAL_ERROR",
                "The local desktop service could not complete the request.",
            )
            return
        self._write_payload(HTTPStatus.OK, payload)

    def _startup_proof(self, method: str) -> FacadePayload:
        # This bootstrap-only oracle is deliberately unavailable to web content.
        # Rust calls it without an Origin before the bearer enters any HTTP request.
        if self.headers.get("Origin") is not None:
            raise RequestContractError(
                "STARTUP_PROOF_ORIGIN_FORBIDDEN",
                "The startup proof is not available to browser origins.",
                status=HTTPStatus.FORBIDDEN,
            )
        if method != "GET":
            raise RequestContractError(
                "METHOD_NOT_ALLOWED",
                "This HTTP method is not allowed.",
                status=HTTPStatus.METHOD_NOT_ALLOWED,
            )
        challenge = str(self.headers.get(STARTUP_CHALLENGE_HEADER) or "")
        if _STARTUP_CHALLENGE.fullmatch(challenge) is None:
            raise RequestContractError(
                "INVALID_STARTUP_CHALLENGE",
                "A fresh 64-character lowercase hexadecimal startup challenge is required.",
                status=HTTPStatus.BAD_REQUEST,
            )
        port = int(self.server.server_port)
        message = f"{STARTUP_PROTOCOL}\n{self.server.facade.mode}\n{port}\n{challenge}"
        proof = hmac.new(
            self.server.startup_proof_key.encode("ascii"),
            message.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()
        return FacadePayload(
            data={"status": "starting", "transport": "loopback", "startupProof": proof}
        )

    def _route(self, method: str, path: str) -> FacadePayload:
        if method == "GET" and path == "/healthz":
            return FacadePayload(
                data={
                    "status": "ok",
                    "transport": "loopback",
                    "authenticated": True,
                }
            )
        if method == "GET" and path == "/api/v1/bootstrap":
            return self.server.facade.bootstrap()

        if method == "GET" and path == "/api/v1/redraft/historical-replay/kha-2026-09-02":
            return self.server.facade.redraft_historical_replay_preview()

        external_intel_match = _REDRAFT_EXTERNAL_INTELLIGENCE.fullmatch(path)
        if method == "GET" and external_intel_match:
            return self.server.facade.redraft_external_intelligence(profile_id=unquote(external_intel_match.group(1)))

        decision_bundle_match = _REDRAFT_DECISION_BUNDLE.fullmatch(path)
        if method == "POST" and decision_bundle_match:
            body = self._json_body(allow_empty=True)
            # positionFilter (owner-test follow-up, section 8): optional,
            # additive -- when supplied, the candidate shortlist is drawn
            # from real eligible players of THAT position specifically
            # (never the default top-8 diversified slice re-filtered
            # client-side, which could falsely report "no candidates" for
            # a position that simply wasn't in that slice).
            self._reject_unknown_fields(body, {"speed", "positionFilter"})
            speed = body.get("speed", "FAST")
            if not isinstance(speed, str):
                raise self._invalid_body("speed must be a string when supplied.")
            position_filter = body.get("positionFilter")
            if position_filter is not None and not isinstance(position_filter, str):
                raise self._invalid_body("positionFilter must be a string when supplied.")
            return self.server.facade.redraft_decision_bundle(
                profile_id=unquote(decision_bundle_match.group(1)), speed=speed,
                position_filter=position_filter,
            )

        decision_bundle_v2_match = _REDRAFT_DECISION_BUNDLE_V2.fullmatch(path)
        if method == "POST" and decision_bundle_v2_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, {"speed"})
            speed = body.get("speed", "FAST")
            if not isinstance(speed, str):
                raise self._invalid_body("speed must be a string when supplied.")
            return self.server.facade.redraft_decision_bundle_v2(
                profile_id=unquote(decision_bundle_v2_match.group(1)), speed=speed,
            )

        if method == "GET" and path == "/api/v1/dynasty/trades":
            return self.server.facade.list_dynasty_trades()

        if method == "GET" and path == "/api/v1/dynasty/workspace":
            return self.server.facade.dynasty_workspace()

        if method == "POST" and path == "/api/v1/dynasty/workspace/personal-board":
            body = self._json_body()
            self._reject_unknown_fields(
                body,
                {"assetId", "watchlist", "target", "avoid", "tags", "notes", "teamWindow"},
            )
            asset_id = body.get("assetId")
            tags = body.get("tags")
            notes = body.get("notes")
            team_window = body.get("teamWindow")
            flags = [body.get("watchlist"), body.get("target"), body.get("avoid")]
            if not isinstance(asset_id, str):
                raise self._invalid_body("assetId must be a string.")
            if any(type(value) is not bool for value in flags):
                raise self._invalid_body("watchlist, target, and avoid must be booleans.")
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
                raise self._invalid_body("tags must be an array of strings.")
            if not isinstance(notes, str) or not isinstance(team_window, str):
                raise self._invalid_body("notes and teamWindow must be strings.")
            return self.server.facade.save_dynasty_personal_entry(
                asset_id=asset_id,
                watchlist=flags[0],
                target=flags[1],
                avoid=flags[2],
                tags=tags,
                notes=notes,
                team_window=team_window,
            )

        if method == "POST" and path == "/api/v1/dynasty/workspace/decisions":
            body = self._json_body()
            self._reject_unknown_fields(
                body,
                {"title", "decisionType", "assetIds", "rationale"},
            )
            title = body.get("title")
            decision_type = body.get("decisionType")
            asset_ids = body.get("assetIds")
            rationale = body.get("rationale")
            if not isinstance(title, str) or not isinstance(decision_type, str):
                raise self._invalid_body("title and decisionType must be strings.")
            if not isinstance(asset_ids, list) or any(
                not isinstance(asset_id, str) for asset_id in asset_ids
            ):
                raise self._invalid_body("assetIds must be an array of strings.")
            if not isinstance(rationale, str):
                raise self._invalid_body("rationale must be a string.")
            return self.server.facade.create_dynasty_decision(
                title=title,
                decision_type=decision_type,
                asset_ids=asset_ids,
                rationale=rationale,
            )

        if method == "POST" and path == "/api/v1/dynasty/workspace/backup":
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            return self.server.facade.backup_dynasty_workspace()

        if method == "POST" and path == "/api/v1/dynasty/workspace/backup/check":
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            return self.server.facade.check_dynasty_workspace_restore()

        if method == "POST" and path == "/api/v1/dynasty/workspace/adopt-legacy":
            body = self._json_body()
            self._reject_unknown_fields(body, {"confirmed"})
            confirmed = body.get("confirmed")
            if type(confirmed) is not bool:
                raise self._invalid_body("confirmed must be a boolean.")
            return self.server.facade.adopt_legacy_dynasty_workspace(confirmed=confirmed)

        if method == "GET" and path.startswith("/api/v1/dynasty/assets/"):
            encoded = path.removeprefix("/api/v1/dynasty/assets/")
            if not encoded or "/" in encoded:
                raise RequestContractError(
                    "ROUTE_NOT_FOUND",
                    "The requested API route was not found.",
                    status=HTTPStatus.NOT_FOUND,
                )
            return self.server.facade.dynasty_asset(unquote(encoded))
        if method == "POST" and path == "/api/v1/dynasty/compare":
            body = self._json_body()
            self._reject_unknown_fields(body, {"assetIds"})
            asset_ids = body.get("assetIds")
            if not isinstance(asset_ids, list):
                raise self._invalid_body("assetIds must be an array.")
            return self.server.facade.compare_dynasty_assets(asset_ids)
        if method == "POST" and path == "/api/v1/dynasty/trades/evaluate":
            body = self._json_body()
            self._reject_unknown_fields(body, {"give", "receive", "get", "teamWindow"})
            if "receive" in body and "get" in body:
                raise self._invalid_body("Use receive without the legacy get alias.")
            give = body.get("give")
            receive = body.get("receive")
            if receive is None and "get" in body:
                receive = body.get("get")
            team_window = body.get("teamWindow")
            if not isinstance(give, list) or not isinstance(receive, list):
                raise self._invalid_body("give and get must be arrays.")
            if not isinstance(team_window, str):
                raise self._invalid_body("teamWindow must be a string.")
            return self.server.facade.evaluate_dynasty_trade(
                give=give,
                receive=receive,
                team_window=team_window,
            )
        if method == "POST" and path == "/api/v1/dynasty/trades/export":
            body = self._json_body()
            self._reject_unknown_fields(
                body,
                {"title", "give", "receive", "teamWindow", "notes"},
            )
            title = body.get("title")
            give = body.get("give")
            receive = body.get("receive")
            team_window = body.get("teamWindow")
            notes = body.get("notes")
            if not isinstance(title, str) or not isinstance(notes, str):
                raise self._invalid_body("title and notes must be strings.")
            if not isinstance(give, list) or not isinstance(receive, list):
                raise self._invalid_body("give and receive must be arrays.")
            if not isinstance(team_window, str):
                raise self._invalid_body("teamWindow must be a string.")
            return self.server.facade.export_dynasty_trade(
                title=title,
                give=give,
                receive=receive,
                team_window=team_window,
                notes=notes,
            )
        if method == "POST" and path == "/api/v1/dynasty/trades":
            body = self._json_body()
            self._reject_unknown_fields(
                body,
                {"scenarioId", "title", "give", "receive", "teamWindow", "notes"},
            )
            scenario_id = body.get("scenarioId")
            title = body.get("title")
            give = body.get("give")
            receive = body.get("receive")
            team_window = body.get("teamWindow")
            notes = body.get("notes")
            if scenario_id is not None and not isinstance(scenario_id, str):
                raise self._invalid_body("scenarioId must be a string or null.")
            if not isinstance(title, str) or not isinstance(notes, str):
                raise self._invalid_body("title and notes must be strings.")
            if not isinstance(give, list) or not isinstance(receive, list):
                raise self._invalid_body("give and receive must be arrays.")
            if not isinstance(team_window, str):
                raise self._invalid_body("teamWindow must be a string.")
            return self.server.facade.save_dynasty_trade(
                scenario_id=scenario_id,
                title=title,
                give=give,
                receive=receive,
                team_window=team_window,
                notes=notes,
            )
        planning_match = _DYNASTY_PLANNING_MODULE.fullmatch(path)
        if method == "POST" and planning_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"checks", "notes"})
            checks = body.get("checks")
            notes = body.get("notes")
            if not isinstance(checks, list):
                raise self._invalid_body("checks must be an array.")
            if not isinstance(notes, str):
                raise self._invalid_body("notes must be a string.")
            return self.server.facade.save_dynasty_planning_module(
                module_id=unquote(planning_match.group(1)),
                checks=checks,
                notes=notes,
            )

        if method == "POST" and path == "/api/v1/redraft/profiles":
            body = self._json_body()
            self._reject_unknown_fields(body, {"presetKey", "leagueName"})
            preset_key = body.get("presetKey")
            league_name = body.get("leagueName")
            if not isinstance(preset_key, str):
                raise self._invalid_body("presetKey must be a string.")
            if league_name is not None and not isinstance(league_name, str):
                raise self._invalid_body("leagueName must be a string when supplied.")
            created = self.server.facade.create_redraft_profile(
                preset_key=preset_key,
                league_name=league_name,
            )
            profile = created.data.get("profile")
            profile_id = profile.get("profileId") if isinstance(profile, dict) else None
            if not isinstance(profile_id, str) or not profile_id:
                raise FacadeError(
                    "REDRAFT_PROFILE_CREATE_FAILED",
                    "The Redraft profile could not be created.",
                    status=HTTPStatus.CONFLICT,
                )
            self.server.facade.activate_redraft_profile(profile_id)
            return self.server.facade.redraft_bootstrap()
        if method == "POST" and path == _SLEEPER_REDRAFT_IMPORT:
            body = self._json_body()
            self._reject_unknown_fields(body, {"leagueId", "username"})
            league_id = body.get("leagueId")
            username = body.get("username")
            if not isinstance(league_id, str) or not isinstance(username, str):
                raise self._invalid_body("leagueId and username must be strings.")
            self.server.facade.import_sleeper_redraft_profile(
                league_id=league_id,
                username=username,
            )
            return self.server.facade.redraft_bootstrap()
        if method == "POST" and path == _KDST_STREAMER:
            body = self._json_body()
            self._reject_unknown_fields(body, {"week"})
            week = body.get("week")
            if type(week) is not int:
                raise self._invalid_body("week must be an integer.")
            return self.server.facade.redraft_kdst_streamer(week=week)
        practical_match = _PRACTICAL_MOCK_START.fullmatch(path)
        if method == "POST" and practical_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            self.server.facade.start_practical_redraft_mock(
                profile_id=unquote(practical_match.group(1))
            )
            return self.server.facade.redraft_bootstrap()
        match = _PROFILE_ACTIVATE.fullmatch(path)
        if method == "POST" and match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            self.server.facade.activate_redraft_profile(unquote(match.group(1)))
            return self.server.facade.redraft_bootstrap()
        duplicate_match = _PROFILE_DUPLICATE.fullmatch(path)
        if method == "POST" and duplicate_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, {"leagueName"})
            league_name = body.get("leagueName")
            if league_name is not None and not isinstance(league_name, str):
                raise self._invalid_body("leagueName must be a string when supplied.")
            self.server.facade.duplicate_redraft_profile(
                unquote(duplicate_match.group(1)),
                league_name=league_name,
            )
            return self.server.facade.redraft_bootstrap()
        nwr_pure_mode_match = _REDRAFT_NWR_PURE_MODE.fullmatch(path)
        if method == "POST" and nwr_pure_mode_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"enabled"})
            enabled = body.get("enabled")
            if not isinstance(enabled, bool):
                raise self._invalid_body("enabled must be a boolean.")
            self.server.facade.set_redraft_nwr_pure_mode(
                profile_id=unquote(nwr_pure_mode_match.group(1)),
                enabled=enabled,
            )
            return self.server.facade.redraft_bootstrap()
        edit_match = _PROFILE_EDIT.fullmatch(path)
        if method == "POST" and edit_match:
            body = self._json_body()
            self._reject_unknown_fields(
                body,
                {"leagueName", "teamCount", "roster", "scoring", "draft", "practicalMode"},
            )
            league_name = body.get("leagueName")
            team_count = body.get("teamCount")
            roster = body.get("roster")
            scoring = body.get("scoring")
            draft = body.get("draft")
            # NWR FINAL PRE-DRAFT GAP CLOSURE: the facade's own
            # `practical_mode` parameter already existed (fixed for the
            # Sleeper-import-only gap in an earlier pass), but no HTTP
            # route ever accepted it, so a manually-configured league
            # (e.g. an ESPN league with real K/DST roster slots -- exactly
            # tonight's real shape) had no way to enable it and Practical
            # Mode-gated ranking generation failed opaquely. Optional and
            # omittable: omitting the field preserves the profile's
            # existing value, unchanged from every prior caller's
            # behavior.
            practical_mode = body.get("practicalMode")
            if practical_mode is not None and not isinstance(practical_mode, bool):
                raise self._invalid_body("practicalMode must be a boolean or omitted.")
            if not isinstance(league_name, str):
                raise self._invalid_body("leagueName must be a string.")
            if type(team_count) is not int:
                raise self._invalid_body("teamCount must be an integer.")
            if not isinstance(roster, dict) or not isinstance(scoring, dict):
                raise self._invalid_body("roster and scoring must be objects.")
            if not isinstance(draft, dict):
                raise self._invalid_body("draft must be an object.")
            self._reject_unknown_fields(
                roster,
                {"qb", "rb", "wr", "te", "flex", "superflex", "k", "dst", "benchSize"},
            )
            self._reject_unknown_fields(
                scoring,
                {"reception", "passingTd", "interception", "tePremium"},
            )
            self._reject_unknown_fields(
                draft,
                {"rounds", "draftSlot", "replacementMethod"},
            )
            if any(type(value) is not int for value in roster.values()):
                raise self._invalid_body("Roster values must be integers.")
            if any(type(value) not in {int, float} for value in scoring.values()):
                raise self._invalid_body("Scoring values must be numbers.")
            if type(draft.get("rounds")) is not int:
                raise self._invalid_body("Draft rounds must be an integer.")
            draft_slot = draft.get("draftSlot")
            if draft_slot is not None and type(draft_slot) is not int:
                raise self._invalid_body("Draft slot must be an integer or null.")
            if not isinstance(draft.get("replacementMethod"), str):
                raise self._invalid_body("replacementMethod must be a string.")
            self.server.facade.update_redraft_profile(
                unquote(edit_match.group(1)),
                league_name=league_name,
                team_count=team_count,
                roster=roster,
                scoring=scoring,
                draft=draft,
                practical_mode=practical_mode,
            )
            return self.server.facade.redraft_bootstrap()
        start_match = _REDRAFT_DRAFT_START.fullmatch(path)
        if method == "POST" and start_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"ownerSlot", "seed", "speed", "mode"})
            if type(body.get("ownerSlot")) is not int or type(body.get("seed")) is not int:
                raise self._invalid_body("ownerSlot and seed must be integers.")
            if not isinstance(body.get("speed"), str) or not isinstance(body.get("mode"), str):
                raise self._invalid_body("speed and mode must be strings.")
            self.server.facade.start_redraft_draft_room(
                profile_id=unquote(start_match.group(1)),
                owner_slot=body["ownerSlot"],
                seed=body["seed"],
                speed=body["speed"],
                mode=body["mode"],
            )
            return self.server.facade.redraft_bootstrap()
        advance_match = _REDRAFT_DRAFT_ADVANCE.fullmatch(path)
        if method == "POST" and advance_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"onePick"})
            if type(body.get("onePick")) is not bool:
                raise self._invalid_body("onePick must be a boolean.")
            self.server.facade.advance_redraft_draft_room(
                profile_id=unquote(advance_match.group(1)),
                one_pick=body["onePick"],
            )
            return self.server.facade.redraft_bootstrap()
        adp_match = _REDRAFT_ADP_IMPORT.fullmatch(path)
        if method == "POST" and adp_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"csvText"})
            if not isinstance(body.get("csvText"), str):
                raise self._invalid_body("csvText must be a string.")
            self.server.facade.import_redraft_adp(
                profile_id=unquote(adp_match.group(1)),
                csv_text=body["csvText"],
            )
            return self.server.facade.redraft_bootstrap()
        adp_refresh_match = _REDRAFT_ADP_REFRESH.fullmatch(path)
        if method == "POST" and adp_refresh_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            self.server.facade.refresh_redraft_adp(
                profile_id=unquote(adp_refresh_match.group(1)),
            )
            return self.server.facade.redraft_bootstrap()
        udk_import_match = _REDRAFT_UDK_IMPORT.fullmatch(path)
        if method == "POST" and udk_import_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"csvText"})
            if not isinstance(body.get("csvText"), str):
                raise self._invalid_body("csvText must be a string.")
            self.server.facade.import_udk_rankings(
                profile_id=unquote(udk_import_match.group(1)),
                csv_text=body["csvText"],
            )
            return self.server.facade.redraft_bootstrap()
        udk_kdst_import_match = _REDRAFT_UDK_KDST_IMPORT.fullmatch(path)
        if method == "POST" and udk_kdst_import_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"csvText"})
            if not isinstance(body.get("csvText"), str):
                raise self._invalid_body("csvText must be a string.")
            self.server.facade.import_udk_kdst_snapshot(
                profile_id=unquote(udk_kdst_import_match.group(1)),
                csv_text=body["csvText"],
            )
            return self.server.facade.redraft_bootstrap()
        udk_rollback_match = _REDRAFT_UDK_ROLLBACK.fullmatch(path)
        if method == "POST" and udk_rollback_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"position"})
            if not isinstance(body.get("position"), str):
                raise self._invalid_body("position must be a string.")
            self.server.facade.rollback_udk_position_rankings(
                profile_id=unquote(udk_rollback_match.group(1)),
                position=body["position"],
            )
            return self.server.facade.redraft_bootstrap()
        if method == "GET" and path == _REDRAFT_STATUS_OVERRIDES:
            return self.server.facade.list_player_status_overrides()
        if method == "POST" and path == _REDRAFT_STATUS_OVERRIDES:
            body = self._json_body()
            allowed = {
                "playerId", "playerName", "kind", "reason", "effectiveDate",
                "verifiedAtUtc", "sources", "correctedTeam",
            }
            self._reject_unknown_fields(body, allowed)
            required_strings = ("playerId", "playerName", "kind", "reason", "effectiveDate", "verifiedAtUtc")
            for field in required_strings:
                if not isinstance(body.get(field), str):
                    raise self._invalid_body(f"{field} must be a string.")
            sources = body.get("sources")
            if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
                raise self._invalid_body("sources must be a list of strings.")
            corrected_team = body.get("correctedTeam", "")
            if not isinstance(corrected_team, str):
                raise self._invalid_body("correctedTeam must be a string when supplied.")
            return self.server.facade.submit_player_status_override(
                player_id=body["playerId"],
                player_name=body["playerName"],
                kind=body["kind"],
                reason=body["reason"],
                effective_date=body["effectiveDate"],
                verified_at_utc=body["verifiedAtUtc"],
                sources=sources,
                corrected_team=corrected_team,
            )
        paste_preview_match = _REDRAFT_PASTE_ADP_PREVIEW.fullmatch(path)
        if method == "POST" and paste_preview_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"pasteText", "selectedSource"})
            if not isinstance(body.get("pasteText"), str) or not isinstance(body.get("selectedSource"), str):
                raise self._invalid_body("pasteText and selectedSource must be strings.")
            return self.server.facade.preview_redraft_paste_adp(
                profile_id=unquote(paste_preview_match.group(1)), paste_text=body["pasteText"],
                selected_source=body["selectedSource"],
            )
        paste_save_match = _REDRAFT_PASTE_ADP_SAVE.fullmatch(path)
        if method == "POST" and paste_save_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"pasteText", "selectedSource", "sourceLabel"})
            if not all(isinstance(body.get(key), str) for key in {"pasteText", "selectedSource", "sourceLabel"}):
                raise self._invalid_body("pasteText, selectedSource, and sourceLabel must be strings.")
            return self.server.facade.save_redraft_paste_adp(
                profile_id=unquote(paste_save_match.group(1)), paste_text=body["pasteText"],
                selected_source=body["selectedSource"], source_label=body["sourceLabel"],
            )
        paste_activate_match = _REDRAFT_PASTE_ADP_ACTIVATE.fullmatch(path)
        if method == "POST" and paste_activate_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            return self.server.facade.activate_redraft_paste_adp(profile_id=unquote(paste_activate_match.group(1)))
        paste_clear_match = _REDRAFT_PASTE_ADP_CLEAR.fullmatch(path)
        if method == "POST" and paste_clear_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            return self.server.facade.clear_redraft_paste_adp(profile_id=unquote(paste_clear_match.group(1)))
        paste_selection_match = _REDRAFT_PASTE_ADP_SELECTION.fullmatch(path)
        if method == "POST" and paste_selection_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"selection"})
            if not isinstance(body.get("selection"), str):
                raise self._invalid_body("selection must be a string.")
            return self.server.facade.set_redraft_owner_platform_selection(
                profile_id=unquote(paste_selection_match.group(1)), selection=body["selection"],
            )
        manual_match = _REDRAFT_PASTE_ADP_MANUAL_MATCH.fullmatch(path)
        if method == "POST" and manual_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"pastedName", "pastedPosition", "pastedPositionRank", "selectedNwrPlayerId", "sourceSnapshotHash"})
            if not all(isinstance(body.get(key), str) for key in {"pastedName", "pastedPosition", "pastedPositionRank", "selectedNwrPlayerId"}):
                raise self._invalid_body("Manual ADP match fields must be strings.")
            return self.server.facade.approve_redraft_owner_platform_manual_match(profile_id=unquote(manual_match.group(1)), pasted_name=body["pastedName"], pasted_position=body["pastedPosition"], pasted_position_rank=body["pastedPositionRank"], selected_nwr_player_id=body["selectedNwrPlayerId"], source_snapshot_hash=str(body.get("sourceSnapshotHash") or ""))
        sleeper_pick_match = _REDRAFT_SLEEPER_PICK.fullmatch(path)
        if method == "POST" and sleeper_pick_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"playerId", "pickNumber"})
            if not isinstance(body.get("playerId"), str) or type(body.get("pickNumber")) is not int:
                raise self._invalid_body("playerId must be a string and pickNumber an integer.")
            self.server.facade.ingest_redraft_sleeper_pick(
                profile_id=unquote(sleeper_pick_match.group(1)),
                player_id=body["playerId"],
                pick_number=body["pickNumber"],
            )
            return self.server.facade.redraft_bootstrap()
        sleeper_sync_match = _REDRAFT_SLEEPER_SYNC.fullmatch(path)
        if method == "POST" and sleeper_sync_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            return self.server.facade.sync_redraft_sleeper_picks(
                profile_id=unquote(sleeper_sync_match.group(1))
            )
        catch_up_preview_match = _REDRAFT_CATCH_UP_PREVIEW.fullmatch(path)
        if method == "POST" and catch_up_preview_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"paste"})
            if not isinstance(body.get("paste"), str):
                raise self._invalid_body("paste must be a string.")
            return self.server.facade.preview_redraft_catch_up(
                profile_id=unquote(catch_up_preview_match.group(1)), paste=body["paste"]
            )
        catch_up_apply_match = _REDRAFT_CATCH_UP_APPLY.fullmatch(path)
        if method == "POST" and catch_up_apply_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"paste"})
            if not isinstance(body.get("paste"), str):
                raise self._invalid_body("paste must be a string.")
            return self.server.facade.apply_redraft_catch_up(
                profile_id=unquote(catch_up_apply_match.group(1)), paste=body["paste"]
            )
        pick_match = _REDRAFT_DRAFT_PICK.fullmatch(path)
        if method == "POST" and pick_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"playerId", "emergencyOverride"})
            profile_id = unquote(pick_match.group(1))
            player_id = body.get("playerId")
            if not isinstance(player_id, str):
                raise self._invalid_body("playerId must be a string.")
            emergency_override = body.get("emergencyOverride", False)
            if not isinstance(emergency_override, bool):
                raise self._invalid_body("emergencyOverride must be a boolean when supplied.")
            self.server.facade.mark_redraft_player(
                profile_id=profile_id,
                player_id=player_id,
                drafted=True,
                emergency_override=emergency_override,
            )
            return self.server.facade.redraft_bootstrap()
        undo_match = _REDRAFT_DRAFT_UNDO.fullmatch(path)
        if method == "POST" and undo_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            self.server.facade.undo_redraft_pick(profile_id=unquote(undo_match.group(1)))
            return self.server.facade.redraft_bootstrap()
        replace_match = _REDRAFT_PICK_REPLACE.fullmatch(path)
        if method == "POST" and replace_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"pickNumber", "playerId"})
            if type(body.get("pickNumber")) is not int or not isinstance(body.get("playerId"), str):
                raise self._invalid_body("pickNumber must be an integer and playerId a string.")
            self.server.facade.replace_redraft_pick(
                profile_id=unquote(replace_match.group(1)),
                pick_number=body["pickNumber"],
                player_id=body["playerId"],
            )
            return self.server.facade.redraft_bootstrap()
        clear_match = _REDRAFT_PICK_CLEAR.fullmatch(path)
        if method == "POST" and clear_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"pickNumber"})
            if type(body.get("pickNumber")) is not int:
                raise self._invalid_body("pickNumber must be an integer.")
            self.server.facade.clear_redraft_pick(
                profile_id=unquote(clear_match.group(1)),
                pick_number=body["pickNumber"],
            )
            return self.server.facade.redraft_bootstrap()
        fill_gap_match = _REDRAFT_PICK_FILL_GAP.fullmatch(path)
        if method == "POST" and fill_gap_match:
            body = self._json_body()
            self._reject_unknown_fields(body, {"pickNumber", "playerId"})
            if type(body.get("pickNumber")) is not int or not isinstance(body.get("playerId"), str):
                raise self._invalid_body("pickNumber must be an integer and playerId a string.")
            self.server.facade.fill_redraft_pick_gap(
                profile_id=unquote(fill_gap_match.group(1)),
                pick_number=body["pickNumber"],
                player_id=body["playerId"],
            )
            return self.server.facade.redraft_bootstrap()
        undo_correction_match = _REDRAFT_PICK_CORRECTION_UNDO.fullmatch(path)
        if method == "POST" and undo_correction_match:
            body = self._json_body(allow_empty=True)
            self._reject_unknown_fields(body, set())
            self.server.facade.undo_redraft_pick_correction(
                profile_id=unquote(undo_correction_match.group(1))
            )
            return self.server.facade.redraft_bootstrap()

        raise RequestContractError(
            "ROUTE_NOT_FOUND",
            "The requested API route was not found.",
            status=HTTPStatus.NOT_FOUND,
        )

    def _validated_path(self) -> str:
        if len(self.path.encode("utf-8", errors="ignore")) > MAX_REQUEST_TARGET_BYTES:
            raise RequestContractError(
                "REQUEST_TARGET_TOO_LARGE",
                "The request target is too large.",
                status=HTTPStatus.REQUEST_URI_TOO_LONG,
            )
        parsed = urlsplit(self.path)
        if parsed.query or parsed.fragment:
            raise RequestContractError(
                "QUERY_NOT_SUPPORTED",
                "Query parameters are not supported by this API route.",
                status=HTTPStatus.BAD_REQUEST,
            )
        return parsed.path

    def _authenticate(self) -> None:
        authorization = self.headers.get("Authorization", "")
        supplied = ""
        if authorization.startswith("Bearer "):
            supplied = authorization.removeprefix("Bearer ").strip()
        elif self.headers.get("X-NWR-Desktop-Token"):
            supplied = str(self.headers.get("X-NWR-Desktop-Token") or "").strip()
        elif self.headers.get("X-NWR-Token"):
            supplied = str(self.headers.get("X-NWR-Token") or "").strip()
        if not supplied:
            raise RequestContractError(
                "AUTHENTICATION_REQUIRED",
                "A desktop API token is required.",
                status=HTTPStatus.UNAUTHORIZED,
            )
        if not hmac.compare_digest(supplied, self.server.api_token):
            raise RequestContractError(
                "AUTHENTICATION_FAILED",
                "The desktop API token is invalid.",
                status=HTTPStatus.FORBIDDEN,
            )

    def _validate_origin(self, *, required: bool) -> None:
        origin = self.headers.get("Origin")
        if not origin:
            if required:
                raise RequestContractError(
                    "ORIGIN_REQUIRED",
                    "An exact local Origin is required for this request.",
                    status=HTTPStatus.FORBIDDEN,
                )
            return
        if origin not in self.server.allowed_origins:
            raise RequestContractError(
                "ORIGIN_NOT_ALLOWED",
                "The request Origin is not allowed.",
                status=HTTPStatus.FORBIDDEN,
            )

    def _enforce_mode_route(self, path: str) -> None:
        if path.startswith("/api/v1/dynasty/") and self.server.facade.mode != "dynasty":
            raise RequestContractError(
                "MODE_ROUTE_UNAVAILABLE",
                "This route is not available in the active desktop mode.",
                status=HTTPStatus.NOT_FOUND,
            )
        if path.startswith("/api/v1/redraft/") and self.server.facade.mode != "redraft":
            raise RequestContractError(
                "MODE_ROUTE_UNAVAILABLE",
                "This route is not available in the active desktop mode.",
                status=HTTPStatus.NOT_FOUND,
            )

    def _json_body(self, *, allow_empty: bool = False) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            if allow_empty:
                return {}
            raise self._invalid_body("A JSON request body is required.")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise self._invalid_body("Content-Length is invalid.") from exc
        if length < 0:
            raise self._invalid_body("Content-Length is invalid.")
        if length > BODY_LIMIT_BYTES:
            raise RequestContractError(
                "REQUEST_BODY_TOO_LARGE",
                "The JSON request body is too large.",
                status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            )
        if length == 0:
            if allow_empty:
                return {}
            raise self._invalid_body("A JSON request body is required.")
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            raise RequestContractError(
                "UNSUPPORTED_MEDIA_TYPE",
                "Content-Type must be application/json.",
                status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            )
        body = self.rfile.read(length)
        try:
            value = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise self._invalid_body("The JSON request body is invalid.") from exc
        if not isinstance(value, dict):
            raise self._invalid_body("The JSON request body must be an object.")
        return value

    def _write_payload(self, status: int, payload: FacadePayload) -> None:
        envelope = contract_envelope(
            self.server.facade.mode,
            data=payload.data,
            warnings=payload.warnings,
        )
        self._write_json(status, envelope)

    def _write_error(self, status: int, code: str, message: str) -> None:
        envelope = contract_envelope(
            self.server.facade.mode,
            data=None,
            errors=[error_contract(code, message)],
        )
        self._write_json(status, envelope)

    def _write_json(self, status: int, value: dict[str, Any]) -> None:
        body = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
        # NWR post-draft overnight, section 24 (real Chrome-rendered UI
        # verification): a real, reproducible client-disconnect crash --
        # a browser aborting a slower in-flight request (e.g. React
        # StrictMode's dev-only double-invoke superseding a still-running
        # DecisionBundle fetch with a fresh one) raises
        # ConnectionAbortedError/BrokenPipeError while this handler is
        # still writing the (by-then-moot) response, which propagated as
        # an unhandled traceback in this connection's own thread --
        # ThreadingHTTPServer keeps serving other connections regardless,
        # but the crash is real, ugly server-log noise for an entirely
        # expected client behavior, unlike every OTHER failure path in
        # this file, which already converts into a clean response via
        # _dispatch's own try/except. There is no one left to respond to
        # at this point, so silently swallowing (not logging a stack
        # trace, not re-raising) is the correct, matching discipline.
        try:
            self.send_response(int(status))
            self._security_headers(content_length=len(body))
            self._cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionAbortedError, BrokenPipeError, ConnectionResetError, OSError):
            pass

    def _security_headers(self, *, content_length: int) -> None:
        self.send_header("Content-Length", str(content_length))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")

    def _cors_headers(self) -> None:
        self.send_header("Vary", "Origin")
        origin = self.headers.get("Origin")
        if origin in self.server.allowed_origins:
            self.send_header("Access-Control-Allow-Origin", str(origin))

    def _method_not_allowed(self) -> None:
        try:
            self._validated_path()
            self._validate_origin(required=False)
            self._authenticate()
        except RequestContractError as exc:
            self._write_error(exc.status, exc.code, exc.message)
            return
        self._write_error(
            HTTPStatus.METHOD_NOT_ALLOWED,
            "METHOD_NOT_ALLOWED",
            "This HTTP method is not allowed.",
        )

    @staticmethod
    def _invalid_body(message: str) -> RequestContractError:
        return RequestContractError(
            "INVALID_REQUEST_BODY",
            message,
            status=HTTPStatus.BAD_REQUEST,
        )

    @classmethod
    def _reject_unknown_fields(cls, body: dict[str, Any], allowed: set[str]) -> None:
        if set(body) - allowed:
            raise cls._invalid_body("The JSON request body contains unsupported fields.")


def validate_bind_host(host: str) -> str:
    text = str(host or "").strip()
    try:
        address = ipaddress.ip_address(text)
    except ValueError as exc:
        raise ValueError("Desktop API host must be an explicit loopback IP address.") from exc
    if not address.is_loopback:
        raise ValueError("Desktop API host must be loopback-only.")
    return address.compressed


def _validate_secret(value: str, *, label: str) -> str:
    value = str(value or "").strip()
    lowered = value.casefold()
    if not MIN_TOKEN_LENGTH <= len(value) <= 512:
        raise ValueError(f"{label} must contain between {MIN_TOKEN_LENGTH} and 512 characters.")
    if not value.isascii() or not all(
        character.isprintable() and not character.isspace() for character in value
    ):
        raise ValueError(f"{label} must contain only printable non-whitespace ASCII characters.")
    if len(set(value)) < 8 or any(
        fragment in lowered for fragment in ("changeme", "password", "replace-me", "token-token")
    ):
        raise ValueError(f"{label} is too weak.")
    return value


def validate_token(token: str) -> str:
    return _validate_secret(token, label="Desktop API token")


def validate_startup_proof_key(key: str) -> str:
    return _validate_secret(key, label="Desktop startup proof key")


def create_desktop_api_server(
    *,
    host: str,
    port: int,
    token: str,
    startup_proof_key: str,
    facade: DesktopBackendFacade,
) -> DesktopApiServer:
    bind_host = validate_bind_host(host)
    if not isinstance(port, int) or not 0 <= port <= 65535:
        raise ValueError("Desktop API port must be between 0 and 65535.")
    validated_token = validate_token(token)
    validated_proof_key = validate_startup_proof_key(startup_proof_key)
    if hmac.compare_digest(validated_token, validated_proof_key):
        raise ValueError("Desktop API token and startup proof key must be distinct.")
    server_type = (
        _IPv6DesktopApiServer if ipaddress.ip_address(bind_host).version == 6 else DesktopApiServer
    )
    if port != 0:
        return server_type(
            (bind_host, port),
            facade=facade,
            token=validated_token,
            startup_proof_key=validated_proof_key,
        )

    last_error: OSError | None = None
    for _ in range(_HIGH_PORT_ATTEMPTS):
        candidate = _HIGH_PORT_MIN + secrets.randbelow(65536 - _HIGH_PORT_MIN)
        try:
            return server_type(
                (bind_host, candidate),
                facade=facade,
                token=validated_token,
                startup_proof_key=validated_proof_key,
            )
        except OSError as exc:
            last_error = exc
    raise OSError(
        f"Unable to bind a random high loopback port after {_HIGH_PORT_ATTEMPTS} attempts."
    ) from last_error
