"""Fail-closed CollegeFootballData REST API v2 adapter.

The adapter does not make a request merely because it is imported. A live call
requires an owner-controlled token already present in an accepted environment
variable, an explicitly allowed v2 path, and an injected transport. This keeps
tests synthetic and prevents credentials from entering command receipts.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

CFBD_BASE_URL = "https://api.collegefootballdata.com"
TOKEN_ENV_NAMES = ("CFBD_BEARER_TOKEN", "BEARER_TOKEN")
MISSING_KEY_STATUS = "BLOCKED_MISSING_OWNER_CONTROLLED_CFBD_KEY"
MAX_LANE_REQUESTS = 800

ALLOWED_ENDPOINTS = {
    "/player/search",
    "/player/season/stats",
    "/player/season",
    "/player/usage",
    "/recruiting/players",
    "/draft/picks",
    "/ppa/players/season",
}


class CfbdContractError(RuntimeError):
    """Raised when a CFBD request violates the owner or endpoint contract."""


class CfbdMissingOwnerKeyError(CfbdContractError):
    """Raised when no accepted owner-controlled token is present."""


class CfbdRequestLimitError(CfbdContractError):
    """Raised before a request would exceed the governed call budget."""


@dataclass(frozen=True)
class CfbdKeyStatus:
    present: bool
    environment_name: str
    status: str


@dataclass(frozen=True)
class CfbdUsage:
    calls_before: int | None
    calls_after: int | None
    calls_made: int
    monthly_limit: int | None
    remaining_before: int | None
    status: str


def key_status(environ: Mapping[str, str] | None = None) -> CfbdKeyStatus:
    """Report only token presence; never return or log the token."""

    source = os.environ if environ is None else environ
    for name in TOKEN_ENV_NAMES:
        if str(source.get(name, "")).strip():
            return CfbdKeyStatus(True, name, "OWNER_CONTROLLED_CFBD_KEY_PRESENT")
    return CfbdKeyStatus(False, "", MISSING_KEY_STATUS)


def token_from_environment(environ: Mapping[str, str] | None = None) -> str:
    """Resolve the token for an explicitly authorized live call."""

    source = os.environ if environ is None else environ
    for name in TOKEN_ENV_NAMES:
        token = str(source.get(name, "")).strip()
        if token:
            return token
    raise CfbdMissingOwnerKeyError(MISSING_KEY_STATUS)


def build_url(path: str, params: Mapping[str, Any] | None = None) -> str:
    if path not in ALLOWED_ENDPOINTS:
        raise CfbdContractError(f"CFBD REST v2 endpoint is not authorized: {path}")
    query = urlencode(
        sorted(
            (str(key), str(value))
            for key, value in (params or {}).items()
            if value is not None
        )
    )
    return f"{CFBD_BASE_URL}{path}" + (f"?{query}" if query else "")


def redacted_request_receipt(
    path: str,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a deterministic request receipt with no authorization material."""

    return {
        "method": "GET",
        "path": path,
        "params": {
            str(key): str(value)
            for key, value in sorted((params or {}).items())
            if value is not None
        },
        "authorization": "BEARER_TOKEN_REDACTED",
        "api_family": "CollegeFootballData REST API v2",
    }


def request_json(
    *,
    path: str,
    params: Mapping[str, Any] | None,
    transport: Callable[..., Any],
    calls_made: int,
    remaining_before: int | None = None,
    monthly_limit: int | None = None,
    environ: Mapping[str, str] | None = None,
) -> Any:
    """Make one injected live request after all fail-closed checks pass."""

    if calls_made >= MAX_LANE_REQUESTS:
        raise CfbdRequestLimitError("CFBD lane request limit would be exceeded")
    if remaining_before is not None:
        stop_at = max(0, int(remaining_before * 0.8))
        if calls_made >= stop_at:
            raise CfbdRequestLimitError("CFBD 80-percent remaining-allowance stop reached")
    if monthly_limit is not None and monthly_limit <= 0:
        raise CfbdRequestLimitError("CFBD monthly limit is unavailable")

    token = token_from_environment(environ)
    url = build_url(path, params)
    response = transport(
        "GET",
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "NWR-New-Evidence-Foundation-V1",
        },
        timeout=30,
    )
    status_code = int(getattr(response, "status_code", 0))
    if status_code < 200 or status_code >= 300:
        raise CfbdContractError(f"CFBD request failed with HTTP {status_code}")
    return response.json()


def synthetic_fixture_is_safe(document: Any) -> bool:
    """Reject fixtures that look like copied bearer credentials."""

    text = str(document)
    lowered = text.lower()
    return (
        "authorization" not in lowered
        and "bearer " not in lowered
        and "cfbd_bearer_token" not in lowered
    )
